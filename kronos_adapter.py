"""Kronos slow-lane adapter for Koda Quant.

This module fetches OHLCV/K-line data from Binance REST and emits a
`macro_filter.json` decision that the fast OFI engine can consume.

It is intentionally safe-by-default:
- If Kronos is installed and `--real-model` (or `KODA_KRONOS_REAL=1`) is used,
  it will run a Kronos forecast.
- Otherwise it falls back to a deterministic OHLCV momentum/volatility heuristic
  with `source=HEURISTIC_OHLCV`, so the pipeline can be tested without model
  weights, Hugging Face access, or a GPU.
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
INTERVAL_MS = {
    "1m": 60_000,
    "3m": 3 * 60_000,
    "5m": 5 * 60_000,
    "15m": 15 * 60_000,
    "30m": 30 * 60_000,
    "1h": 60 * 60_000,
    "2h": 2 * 60 * 60_000,
    "4h": 4 * 60 * 60_000,
    "1d": 24 * 60 * 60_000,
}


@dataclass(frozen=True)
class Kline:
    open_time_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float


@dataclass(frozen=True)
class MacroFilterDecision:
    bias: str
    confidence: float
    forecast_return: float
    horizon: str
    symbol: str
    interval: str
    lookback: int
    pred_len: int
    max_risk_multiplier: float
    source: str
    updated_at: int
    expires_at: int
    reason: str


class KronosAdapter:
    """Fetch Binance OHLCV and emit Koda-compatible macro filter decisions."""

    def __init__(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "15m",
        lookback: int = 512,
        pred_len: int = 4,
        out_file: str = "macro_filter.json",
        use_real_model: bool | None = None,
        model_name: str = "NeoQuasar/Kronos-small",
        tokenizer_name: str = "NeoQuasar/Kronos-Tokenizer-base",
        max_context: int = 512,
        device: str = "cpu",
    ):
        if interval not in INTERVAL_MS:
            supported = ", ".join(sorted(INTERVAL_MS))
            raise ValueError(f"Unsupported interval '{interval}'. Supported intervals: {supported}")
        if lookback < 20:
            raise ValueError("lookback must be >= 20 for stable macro classification")
        if pred_len < 1:
            raise ValueError("pred_len must be >= 1")

        self.symbol = symbol.upper()
        self.interval = interval
        self.lookback = lookback
        self.pred_len = pred_len
        self.out_file = Path(out_file)
        self.use_real_model = env_flag("KODA_KRONOS_REAL", default=False) if use_real_model is None else use_real_model
        self.model_name = model_name
        self.tokenizer_name = tokenizer_name
        self.max_context = max_context
        self.device = device

    def run_once(self) -> MacroFilterDecision:
        klines = fetch_binance_ohlcv(self.symbol, self.interval, self.lookback)
        if self.use_real_model and self._kronos_dependencies_available():
            decision = self._run_kronos_forecast(klines)
        else:
            decision = self._run_heuristic_forecast(klines)
        write_macro_filter(decision, self.out_file)
        return decision

    def _kronos_dependencies_available(self) -> bool:
        maybe_repo_path = os.environ.get("KRONOS_REPO_PATH", "").strip()
        if maybe_repo_path and maybe_repo_path not in sys.path:
            sys.path.insert(0, maybe_repo_path)
        return importlib.util.find_spec("model") is not None and importlib.util.find_spec("pandas") is not None

    def _run_kronos_forecast(self, klines: Sequence[Kline]) -> MacroFilterDecision:
        import pandas as pd
        from model import Kronos, KronosPredictor, KronosTokenizer

        tokenizer = KronosTokenizer.from_pretrained(self.tokenizer_name)
        model = Kronos.from_pretrained(self.model_name)
        predictor_kwargs = {"max_context": self.max_context}
        if "device" in inspect.signature(KronosPredictor).parameters:
            predictor_kwargs["device"] = self.device
        predictor = KronosPredictor(model, tokenizer, **predictor_kwargs)

        rows = [asdict(kline) for kline in klines]
        df = pd.DataFrame(rows)
        x_df = df[["open", "high", "low", "close", "volume", "amount"]]
        x_timestamp = pd.to_datetime(df["open_time_ms"], unit="ms")
        y_timestamp = pd.to_datetime(
            build_future_open_times(klines[-1].open_time_ms, self.interval, self.pred_len),
            unit="ms",
        )
        pred_df = predictor.predict(
            df=x_df,
            x_timestamp=x_timestamp,
            y_timestamp=y_timestamp,
            pred_len=self.pred_len,
            T=1.0,
            top_p=0.9,
            sample_count=1,
        )
        forecast_closes = [float(value) for value in pred_df["close"].tolist()]
        return classify_forecast(
            klines=klines,
            forecast_closes=forecast_closes,
            symbol=self.symbol,
            interval=self.interval,
            pred_len=self.pred_len,
            source="KRONOS",
        )

    def _run_heuristic_forecast(self, klines: Sequence[Kline]) -> MacroFilterDecision:
        forecast_closes = heuristic_forecast_closes(klines, self.pred_len)
        source = "HEURISTIC_OHLCV"
        reason = "Kronos dependencies not active; used deterministic OHLCV momentum/volatility fallback."
        decision = classify_forecast(
            klines=klines,
            forecast_closes=forecast_closes,
            symbol=self.symbol,
            interval=self.interval,
            pred_len=self.pred_len,
            source=source,
        )
        return MacroFilterDecision(**{**asdict(decision), "reason": reason})


def env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def fetch_binance_ohlcv(symbol: str, interval: str, limit: int) -> List[Kline]:
    params = urllib.parse.urlencode({"symbol": symbol.upper(), "interval": interval, "limit": limit})
    url = f"{BINANCE_KLINES_URL}?{params}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [parse_binance_kline(row) for row in payload]


def parse_binance_kline(row: Sequence[object]) -> Kline:
    return Kline(
        open_time_ms=int(row[0]),
        open=float(row[1]),
        high=float(row[2]),
        low=float(row[3]),
        close=float(row[4]),
        volume=float(row[5]),
        amount=float(row[7]),
    )


def build_future_open_times(last_open_time_ms: int, interval: str, pred_len: int) -> List[int]:
    step = INTERVAL_MS[interval]
    return [last_open_time_ms + step * i for i in range(1, pred_len + 1)]


def heuristic_forecast_closes(klines: Sequence[Kline], pred_len: int) -> List[float]:
    closes = [kline.close for kline in klines]
    log_returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes)) if closes[i - 1] > 0]
    recent = log_returns[-12:] or log_returns[-1:] or [0.0]
    weights = list(range(1, len(recent) + 1))
    weighted_momentum = sum(ret * weight for ret, weight in zip(recent, weights)) / sum(weights)
    volatility = standard_deviation(recent)
    damped_step = clamp(weighted_momentum, -2.0 * volatility, 2.0 * volatility) if volatility > 0 else weighted_momentum

    forecasts = []
    price = closes[-1]
    for _ in range(pred_len):
        price *= math.exp(damped_step)
        forecasts.append(price)
    return forecasts


def classify_forecast(
    klines: Sequence[Kline],
    forecast_closes: Sequence[float],
    symbol: str,
    interval: str,
    pred_len: int,
    source: str,
) -> MacroFilterDecision:
    last_close = float(klines[-1].close)
    forecast_close = float(forecast_closes[-1])
    forecast_return = (forecast_close / last_close) - 1.0
    abs_return = abs(forecast_return)

    if forecast_return > 0.0015:
        bias = "BULL"
    elif forecast_return < -0.0015:
        bias = "BEAR"
    else:
        bias = "NEUTRAL"

    confidence = round(clamp(0.50 + abs_return * 50.0, 0.50, 0.90), 3)
    max_risk_multiplier = risk_multiplier_for_bias(bias, confidence)
    updated_at = int(time.time())
    expires_at = updated_at + max(INTERVAL_MS[interval] * pred_len // 1000, 60)
    reason = f"{source} forecast_return={forecast_return:.5f}; bias={bias}; confidence={confidence:.3f}"
    return MacroFilterDecision(
        bias=bias,
        confidence=confidence,
        forecast_return=round(forecast_return, 6),
        horizon=f"{pred_len}x{interval}",
        symbol=symbol.upper(),
        interval=interval,
        lookback=len(klines),
        pred_len=pred_len,
        max_risk_multiplier=max_risk_multiplier,
        source=source,
        updated_at=updated_at,
        expires_at=expires_at,
        reason=reason,
    )


def risk_multiplier_for_bias(bias: str, confidence: float) -> float:
    if bias == "NEUTRAL":
        return 1.0
    if bias == "BULL":
        return round(clamp(0.9 + confidence * 0.35, 1.0, 1.2), 2)
    return round(clamp(1.05 - confidence * 0.35, 0.7, 1.0), 2)


def standard_deviation(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def write_macro_filter(decision: MacroFilterDecision, out_file: Path) -> None:
    out_file.write_text(json.dumps(asdict(decision), indent=2, ensure_ascii=False), encoding="utf-8")


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Koda macro_filter.json from Binance OHLCV + Kronos/heuristic forecast.")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="15m", choices=sorted(INTERVAL_MS))
    parser.add_argument("--lookback", type=int, default=512)
    parser.add_argument("--pred-len", type=int, default=4)
    parser.add_argument("--out", default="macro_filter.json")
    parser.add_argument("--real-model", action="store_true", help="Use installed Kronos model instead of heuristic fallback.")
    parser.add_argument("--model-name", default="NeoQuasar/Kronos-small")
    parser.add_argument("--tokenizer-name", default="NeoQuasar/Kronos-Tokenizer-base")
    parser.add_argument("--device", default="cpu")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> MacroFilterDecision:
    args = parse_args(argv)
    adapter = KronosAdapter(
        symbol=args.symbol,
        interval=args.interval,
        lookback=args.lookback,
        pred_len=args.pred_len,
        out_file=args.out,
        use_real_model=args.real_model,
        model_name=args.model_name,
        tokenizer_name=args.tokenizer_name,
        device=args.device,
    )
    decision = adapter.run_once()
    print(json.dumps(asdict(decision), indent=2, ensure_ascii=False))
    return decision


if __name__ == "__main__":
    main()
