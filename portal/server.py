# siemnest portal - stdlib only.
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORTAL_PORT", "8080"))
GRAYLOG_URL = os.environ.get("GRAYLOG_URL", "http://127.0.0.1:9000")
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "https://127.0.0.1:443")
AI_URL = os.environ.get("AI_URL", "http://127.0.0.1:8090")
ROOT = os.path.dirname(os.path.abspath(__file__))


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/healthz":
            return self._send(200, "text/plain", b"ok")
        if path in ("/", ""):
            path = "/index.html"
        safe = os.path.normpath(path).lstrip("/")
        full = os.path.join(ROOT, safe)
        if not full.startswith(ROOT) or not os.path.isfile(full):
            return self._send(404, "text/plain", b"not found")
        ctype = "text/html" if full.endswith(".html") else "text/plain"
        try:
            with open(full, "rb") as f:
                body = f.read()
            if full.endswith(".html"):
                body = (body.replace(b"__GRAYLOG_URL__", GRAYLOG_URL.encode())
                            .replace(b"__DASHBOARD_URL__", DASHBOARD_URL.encode())
                            .replace(b"__AI_URL__", AI_URL.encode()))
            return self._send(200, ctype, body)
        except OSError:
            return self._send(404, "text/plain", b"not found")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"[siemnest] portal on 0.0.0.0:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
