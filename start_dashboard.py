"""Local static server for Koda Quant dashboard.

Run:
  python start_dashboard.py
Then open:
  http://localhost:<port>/index.html
"""

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

HOST = "0.0.0.0"
DEFAULT_PORT = 8000
MAX_PORT_TRIES = 20


def bind_server(start_port: int):
    last_error = None
    for port in range(start_port, start_port + MAX_PORT_TRIES):
        try:
            return ThreadingHTTPServer((HOST, port), SimpleHTTPRequestHandler), port
        except OSError as exc:
            last_error = exc
    raise RuntimeError(
        f"[KODA] Failed to bind any port from {start_port} to {start_port + MAX_PORT_TRIES - 1}"
    ) from last_error


if __name__ == "__main__":
    server, port = bind_server(DEFAULT_PORT)
    print(f"[KODA] Dashboard server running on http://localhost:{port}/index.html")
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
