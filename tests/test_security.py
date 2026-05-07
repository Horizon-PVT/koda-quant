"""
Security Tests for Koda Quant HFT System
Tests: Dashboard Auth (fail-closed, rate-limit, correct/wrong password)
       Backend Safety Gate (SIMULATED when gate is off)
"""
import pytest
import os
import sys
import base64
from unittest.mock import patch, MagicMock
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------
# 1. Dashboard Auth Tests (start_dashboard.py)
# ---------------------------------------------------------
import start_dashboard


class FakeHeaders(dict):
    """Minimal mock for http.server headers."""
    def get(self, key, default=None):
        return super().get(key, default)


class FakeHandler:
    """Lightweight stand-in for ProxyHTTPRequestHandler."""
    def __init__(self, headers):
        self.headers = headers

    def check_auth(self):
        return start_dashboard.ProxyHTTPRequestHandler.check_auth(self)


# --- Fail-closed ---
def test_auth_fail_closed_when_no_password():
    """P0: If DASHBOARD_PASS is empty the server must refuse access."""
    start_dashboard.DASHBOARD_PASS = ""
    handler = FakeHandler(FakeHeaders())
    assert handler.check_auth() is False


# --- Missing Authorization header ---
def test_auth_rejects_missing_header():
    start_dashboard.DASHBOARD_PASS = "Secret123"
    handler = FakeHandler(FakeHeaders())          # no Authorization key
    assert handler.check_auth() is False


# --- Wrong password triggers delay ---
def test_auth_rejects_wrong_password_with_delay():
    start_dashboard.DASHBOARD_PASS = "Secret123"
    start_dashboard.DASHBOARD_USER = "admin"
    creds = base64.b64encode(b"admin:wrongpassword").decode()
    handler = FakeHandler(FakeHeaders({"Authorization": f"Basic {creds}"}))
    with patch("time.sleep") as mock_sleep:
        assert handler.check_auth() is False
        mock_sleep.assert_called_once_with(2)


# --- Correct password ---
def test_auth_accepts_correct_password():
    start_dashboard.DASHBOARD_PASS = "Secret123"
    start_dashboard.DASHBOARD_USER = "admin"
    creds = base64.b64encode(b"admin:Secret123").decode()
    handler = FakeHandler(FakeHeaders({"Authorization": f"Basic {creds}"}))
    assert handler.check_auth() is True


# --- Server refuses to start on public binding without password ---
def test_bind_server_raises_without_password():
    start_dashboard.HOST = "0.0.0.0"
    start_dashboard.DASHBOARD_PASS = ""
    with pytest.raises(RuntimeError, match="DASHBOARD_PASS is required"):
        start_dashboard.bind_server(8001)


# ---------------------------------------------------------
# 2. Backend Safety Gate Tests (ai_brain.py)
#    ai_brain calls sys.exit(1) on import when QWEN_API_KEY
#    is missing, so we patch os.environ and sys.exit before
#    importing.
# ---------------------------------------------------------

@pytest.fixture(scope="module")
def engine_class():
    """Import OFIV5SniperEngine safely even without real API keys."""
    env_patch = {
        "QWEN_API_KEY": "test-key-placeholder",
        "BINANCE_API_KEY": "",
        "BINANCE_SECRET_KEY": "",
    }
    with patch.dict(os.environ, env_patch):
        # Prevent real sys.exit if something still triggers it
        with patch.object(sys, "exit"):
            # Force re-import to pick up patched env
            if "ai_brain" in sys.modules:
                del sys.modules["ai_brain"]
            import ai_brain
            yield ai_brain.OFIV5SniperEngine


def _make_engine(engine_class, live_cfg):
    """Create a bare engine with custom live_cfg, bypassing heavy init."""
    with patch.object(engine_class, "__init__", lambda self, *a, **kw: None):
        eng = engine_class.__new__(engine_class)
        eng.live_cfg = live_cfg
    return eng


def test_gate_simulates_when_env_missing(engine_class):
    """Order must be SIMULATED when KODA_ENABLE_LIVE_TRADING is unset."""
    eng = _make_engine(engine_class, {"allow_live_trading": True})
    with patch.dict(os.environ, {}, clear=True):
        res = eng.execute_binance_request(
            "POST", "/fapi/v1/order",
            {"symbol": "BTCUSDT", "side": "BUY"},
        )
    assert res["status"] == "SIMULATED"
    assert "Safety gate active" in res.get("msg", "")


def test_gate_simulates_when_config_false(engine_class):
    """Order must be SIMULATED when allow_live_trading is False."""
    eng = _make_engine(engine_class, {"allow_live_trading": False})
    with patch.dict(os.environ, {"KODA_ENABLE_LIVE_TRADING": "true"}):
        res = eng.execute_binance_request(
            "POST", "/fapi/v1/order",
            {"symbol": "BTCUSDT", "side": "BUY"},
        )
    assert res["status"] == "SIMULATED"
    assert "Safety gate active" in res.get("msg", "")


def test_gate_simulates_lowercase_post(engine_class):
    """method.upper() must catch lowercase 'post' too."""
    eng = _make_engine(engine_class, {"allow_live_trading": False})
    with patch.dict(os.environ, {"KODA_ENABLE_LIVE_TRADING": "false"}):
        res = eng.execute_binance_request(
            "post", "/fapi/v1/order",
            {"symbol": "BTCUSDT", "side": "BUY"},
        )
    assert res["status"] == "SIMULATED"


def test_gate_passes_when_both_enabled(engine_class):
    """When both env + config are enabled, gate must NOT block."""
    eng = _make_engine(engine_class, {"allow_live_trading": True})
    import ai_brain
    ai_brain.binance_api_key = "fake"
    ai_brain.binance_secret_key = "fake"

    with patch.dict(os.environ, {"KODA_ENABLE_LIVE_TRADING": "true"}):
        with patch("urllib.request.urlopen") as mock_open:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'{"status":"LIVE_OK"}'
            mock_open.return_value.__enter__.return_value = mock_resp
            res = eng.execute_binance_request(
                "POST", "/fapi/v1/order",
                {"symbol": "BTCUSDT", "side": "BUY"},
            )
    assert res.get("status") != "SIMULATED"
