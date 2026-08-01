"""Vercel serverless reverse proxy for the Telegram Bot API.

Forwards any method/path/body under /bot<TOKEN>/<method> to
https://api.telegram.org unchanged. Exists because api.telegram.org is
network-blocked from the origin server; Vercel Serverless Functions run in a
fixed region (not the caller-nearest edge like Cloudflare Workers), so they
don't inherit that block.
"""
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler

TARGET = "https://api.telegram.org"
TIMEOUT = 25


class handler(BaseHTTPRequestHandler):
    def _proxy(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else None
        headers = {}
        if "Content-Type" in self.headers:
            headers["Content-Type"] = self.headers["Content-Type"]

        url = TARGET + self.path
        req = urllib.request.Request(url, data=body, method=self.command, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.end_headers()
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_GET(self):
        self._proxy()

    def do_POST(self):
        self._proxy()
