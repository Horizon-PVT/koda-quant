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
        {"pnl": -5},
        {"pnl": -3},
        {"pnl": -2},
        {"pnl": -1},
        {"pnl": 1},
    ]
    pd.DataFrame(rows).to_csv(tmp_path / "trade_history.csv", index=False)

    result = adaptive_engine.update_adaptive_rules("trade_history.csv")

    assert 2.0 <= result["z_threshold"] <= 4.0
    assert 0.5 <= result["risk_multiplier"] <= 1.5
    saved = json.loads(Path("adaptive_config.json").read_text())
    assert saved == result
