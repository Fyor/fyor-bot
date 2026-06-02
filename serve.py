#!/usr/bin/env python3
"""
Simple HTTP server for the Lundby interactive map.
Run:  python3 serve.py
Then open:  http://localhost:8080
"""
import http.server, socketserver, os, sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
PUBLIC = os.path.join(os.path.dirname(__file__), "public")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC, **kwargs)
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} {fmt % args}")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"\n  Lundby Map → http://localhost:{PORT}\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
