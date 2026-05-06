"""Local static server for Koda Quant dashboard.

Run:
  python start_dashboard.py
Then open:
  http://localhost:8000/index.html
"""

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

HOST = "0.0.0.0"
PORT = 8000

if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), SimpleHTTPRequestHandler)
    print(f"[KODA] Dashboard server running on http://localhost:{PORT}/index.html")
    print("[KODA] Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("[KODA] Server stopped")
