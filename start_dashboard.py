"""Local static server for Koda Quant dashboard with secure API proxy.

Run:
  python start_dashboard.py
Then open:
  http://localhost:<port>/index.html
"""

import os
import time
import json
import urllib.request
import urllib.parse
import hmac
import hashlib
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from dotenv import load_dotenv

# Load API Keys
load_dotenv(".env")
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY", "")

HOST = "0.0.0.0"  # P1 FIX: Bind to all interfaces for VPS public access.
DEFAULT_PORT = 8001
MAX_PORT_TRIES = 20

def binance_request(endpoint):
    if not BINANCE_API_KEY or not BINANCE_SECRET_KEY:
        return {"status": "ERROR", "msg": "Missing API Keys in .env"}
        
    base_url = "https://fapi.binance.com"
    params = {"timestamp": int(time.time() * 1000)}
    query_string = urllib.parse.urlencode(params)
    signature = hmac.new(BINANCE_SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
    
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("X-MBX-APIKEY", BINANCE_API_KEY)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {"status": "ERROR", "msg": str(e)}

import base64
import time
import threading

DASHBOARD_PASS = os.environ.get("DASHBOARD_PASS", "")
DASHBOARD_USER = os.environ.get("DASHBOARD_USER", "admin")

# ── IP-based Rate Limiter (thread-safe) ──────────────────
# Tracks failed auth attempts per IP. Locks out an IP for
# LOCKOUT_SECONDS after MAX_FAILS within WINDOW_SECONDS.
_rate_lock = threading.Lock()
_fail_buckets = {}          # ip -> [timestamp, timestamp, ...]
MAX_FAILS = 5               # max failures before lockout
WINDOW_SECONDS = 60         # rolling window
LOCKOUT_SECONDS = 300       # 5 min lockout after exceeding limit


def _is_rate_limited(ip: str) -> bool:
    """Return True if this IP should be blocked (429)."""
    now = time.time()
    with _rate_lock:
        attempts = _fail_buckets.get(ip, [])
        # Prune old entries outside the window
        attempts = [t for t in attempts if now - t < WINDOW_SECONDS]
        _fail_buckets[ip] = attempts

        if len(attempts) >= MAX_FAILS:
            # Check if still in lockout period from the last fail
            if now - attempts[-1] < LOCKOUT_SECONDS:
                return True
            # Lockout expired — reset bucket
            _fail_buckets[ip] = []
    return False


def _record_fail(ip: str):
    """Record a failed auth attempt for this IP."""
    with _rate_lock:
        _fail_buckets.setdefault(ip, []).append(time.time())


class ProxyHTTPRequestHandler(SimpleHTTPRequestHandler):
    # P1 FIX: Block sensitive files from being served
    BLOCKED_FILES = {'.env', 'trade_history.csv', 'adaptive_config.json', 
                     'macro_filter.json', 'koda_v8_upgrade.patch'}
    
    def _client_ip(self):
        """Get the client IP from the request."""
        return self.client_address[0] if self.client_address else "unknown"

    def check_auth(self):
        if not DASHBOARD_PASS:
            print("[SECURITY WARNING] DASHBOARD_PASS is not set; refusing dashboard access (fail-closed).")
            return False

        # Rate limit check BEFORE even looking at credentials
        ip = self._client_ip()
        if _is_rate_limited(ip):
            return "RATE_LIMITED"

        auth_header = self.headers.get('Authorization')
        if auth_header is None:
            return False
        if not auth_header.startswith('Basic '):
            _record_fail(ip)
            return False
        try:
            encoded_credentials = auth_header.split(' ')[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded_credentials.split(':', 1)
            
            if username == DASHBOARD_USER and password == DASHBOARD_PASS:
                return True
            else:
                _record_fail(ip)
                return False
        except Exception:
            _record_fail(ip)
            return False

    def do_GET(self):
        # Enforce Basic Auth
        auth_result = self.check_auth()
        if auth_result == "RATE_LIMITED":
            self.send_response(429)
            self.send_header('Content-type', 'text/html')
            self.send_header('Retry-After', str(LOCKOUT_SECONDS))
            self.end_headers()
            self.wfile.write(b"429 Too Many Requests - IP temporarily locked")
            return
        if not auth_result:
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Koda Quant Dashboard"')
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"401 Unauthorized")
            return
            
        # Block sensitive files
        requested_file = os.path.basename(self.path.split('?')[0])
        if requested_file in self.BLOCKED_FILES:
            self.send_error(403, "Forbidden")
            return
            
        if self.path == '/api/portfolio':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Fetch Account Info (Balance & Unrealized PnL)
            account_data = binance_request("/fapi/v2/account")
            # Fetch Position Risk (Open Positions)
            position_data = binance_request("/fapi/v2/positionRisk")
            
            response_data = {
                "account": account_data,
                "positions": position_data
            }
            
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return
            
        if self.path == '/api/history':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            history = []
            if os.path.exists("trade_history.csv"):
                import csv
                try:
                    with open("trade_history.csv", newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        history = list(reader)
                except Exception as e:
                    history = [{"error": str(e)}]
            self.wfile.write(json.dumps(history).encode('utf-8'))
            return
            
        # Serve static files for all other paths
        super().do_GET()

def bind_server(start_port: int):
    if HOST == "0.0.0.0" and not DASHBOARD_PASS:
        raise RuntimeError("DASHBOARD_PASS is required for public dashboard binding. Set it in .env to proceed.")
        
    last_error = None
    for port in range(start_port, start_port + MAX_PORT_TRIES):
        try:
            return ThreadingHTTPServer((HOST, port), ProxyHTTPRequestHandler), port
        except OSError as exc:
            last_error = exc
    raise RuntimeError(
        f"[KODA] Failed to bind any port from {start_port} to {start_port + MAX_PORT_TRIES - 1}"
    ) from last_error

if __name__ == "__main__":
    server, port = bind_server(DEFAULT_PORT)
    print(f"[KODA] Dashboard server with API Proxy running on http://localhost:{port}/index.html")
    if port != DEFAULT_PORT:
        print(f"[KODA] Port {DEFAULT_PORT} is busy. Auto-switched to {port}.")
    print("[KODA] Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("[KODA] Server stopped")
