#!/usr/bin/env python3
"""
AntiWatermark Web Server
========================
Zero-dependency local HTTP server serving the interactive UI and REST API.
"""

import http.server
import socketserver
import os
import sys
import json
from antiwatermark.core import clean_text

PORT = 8000
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')


class AntiwatermarkHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_POST(self):
        if self.path == '/api/sanitize':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                raw_text = data.get('text', '')
            except Exception:
                raw_text = body

            cleaned, scorecard = clean_text(raw_text)
            scorecard['sanitized_text'] = cleaned

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(scorecard).encode('utf-8'))
        else:
            self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), AntiwatermarkHandler) as httpd:
        print("==============================================================")
        print(f"🌐 AntiWatermark Web UI is live at: http://localhost:{PORT}")
        print("==============================================================")
        print("• Interactive web app with real-time AI detector scorecard.")
        print("• REST API available at: POST http://localhost:8000/api/sanitize")
        print("• Press Ctrl+C to stop the server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped.")


if __name__ == '__main__':
    run_server()
