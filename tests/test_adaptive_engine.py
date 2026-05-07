import pytest

pytest.importorskip("pandas")

import json
from pathlib import Path

import pandas as pd

import adaptive_engine


def test_update_adaptive_rules_without_csv_returns_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = adaptive_engine.update_adaptive_rules("missing.csv")
    assert result["z_threshold"] == 2.5
    assert result["risk_multiplier"] == 1.0


def test_update_adaptive_rules_clamps_and_writes_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    rows = [
        {"pnl": -5, "z_ofi": 2.1, "spread": 0.001, "volatility": 15.0, "price": 60000, "signal": "BUY"},
        {"pnl": -3, "z_ofi": 2.1, "spread": 0.001, "volatility": 15.0, "price": 60000, "signal": "BUY"},
        {"pnl": -2, "z_ofi": 2.1, "spread": 0.001, "volatility": 15.0, "price": 60000, "signal": "BUY"},
        {"pnl": -1, "z_ofi": 2.1, "spread": 0.001, "volatility": 15.0, "price": 60000, "signal": "BUY"},
        {"pnl": 1, "z_ofi": 2.1, "spread": 0.001, "volatility": 15.0, "price": 60000, "signal": "BUY"},
    ]
    pd.DataFrame(rows).to_csv(tmp_path / "trade_history.csv", index=False)

    result = adaptive_engine.update_adaptive_rules("trade_history.csv")

    assert 2.0 <= result["z_threshold"] <= 4.0
    assert 0.5 <= result["risk_multiplier"] <= 1.5
    saved = json.loads(Path("adaptive_config.json").read_text())
    assert saved == result
