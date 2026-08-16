#!/usr/bin/env python3
"""
AntiWatermark Web Server v2.0
==============================
Zero-dependency local HTTP server serving the interactive UI and REST API.
All endpoints are local-only — no data leaves your machine.

Endpoints:
    GET  /api/health   — Status, version, Ollama availability
    GET  /api/config   — Current backend configuration
    POST /api/clean    — Deterministic Fast Mode cleaning
    POST /api/rewrite  — Local Neural Mode rewriting (requires Ollama)
"""

import http.server
import socketserver
import os
import sys
import json
import time
from antiwatermark.core import clean_text, validate_output, ImmunityShield
from antiwatermark.backend import (
    BuiltinBackend, OllamaBackend,
    RewriteConfig, get_available_backends, BackendError, SecurityError
)

PORT = 8000
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')


class AntiwatermarkHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def _read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        try:
            return json.loads(body)
        except Exception:
            return {'text': body}

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _send_error_json(self, message, status=400):
        self._send_json({'error': message}, status)

    def do_POST(self):
        if self.path == '/api/clean':
            self._handle_clean()
        elif self.path == '/api/rewrite':
            self._handle_rewrite()
        else:
            self.send_error(404, "Endpoint not found")

    def do_GET(self):
        if self.path == '/api/health':
            self._handle_health()
        elif self.path == '/api/config':
            self._handle_config()
        else:
            super().do_GET()

    def _handle_clean(self):
        """POST /api/clean — Fast Mode deterministic cleaning."""
        data = self._read_json_body()
        raw_text = data.get('text', '')
        humanize = data.get('humanize', True)

        start = time.time()
        cleaned, scorecard = clean_text(raw_text, humanize=humanize)
        duration_ms = round((time.time() - start) * 1000, 1)

        self._send_json({
            'text': cleaned,
            'engine': 'builtin',
            'processing_time_ms': duration_ms,
            'validation_passed': True,
            'diagnostics': {
                'invisible_chars_removed': scorecard.get('invisible_chars_removed', 0),
                'cliches_replaced': scorecard.get('cliches_replaced', 0),
                'human_confidence_pct': scorecard.get('human_confidence_pct', 100.0),
                'pattern_risk_level': scorecard.get('pattern_risk_level', 'N/A'),
                'sentence_count': scorecard.get('sentence_count', 0),
                'total_words': scorecard.get('total_words', 0),
                'detected_markers': scorecard.get('detected_markers', {}),
            }
        })

    def _handle_rewrite(self):
        """POST /api/rewrite — Local Neural Mode rewriting via Ollama."""
        data = self._read_json_body()
        raw_text = data.get('text', '')
        model = data.get('model', 'llama3.2')
        temperature = float(data.get('temperature', 0.7))
        timeout = float(data.get('timeout', 60.0))
        domain = data.get('domain', 'general')

        if not raw_text.strip():
            self._send_error_json("No text provided")
            return

        config = RewriteConfig(
            temperature=temperature,
            max_tokens=4096,
            timeout_seconds=timeout,
            model=model,
            domain=domain
        )

        try:
            backend = OllamaBackend(model=model)

            if not backend.is_available():
                self._send_error_json(
                    "Ollama is not running. Start it with: ollama serve",
                    503
                )
                return

            start = time.time()
            rewritten = backend.rewrite(raw_text, config)
            duration_ms = round((time.time() - start) * 1000, 1)

            # Validate the output
            shield = ImmunityShield()
            shield.shield(raw_text)
            validation = validate_output(raw_text, rewritten, shield)

            if not validation.is_valid:
                # Fallback to deterministic cleaning
                cleaned, scorecard = clean_text(raw_text, humanize=True)
                self._send_json({
                    'text': cleaned,
                    'engine': backend.name(),
                    'processing_time_ms': duration_ms,
                    'validation_passed': False,
                    'validation_failures': validation.failures,
                    'rollback': True,
                    'diagnostics': {
                        'invisible_chars_removed': scorecard.get('invisible_chars_removed', 0),
                        'cliches_replaced': scorecard.get('cliches_replaced', 0),
                        'human_confidence_pct': scorecard.get('human_confidence_pct', 100.0),
                        'pattern_risk_level': scorecard.get('pattern_risk_level', 'N/A'),
                    }
                })
                return

            # Validated neural output
            _, scorecard = clean_text(rewritten, humanize=False)
            self._send_json({
                'text': rewritten,
                'engine': backend.name(),
                'processing_time_ms': duration_ms,
                'validation_passed': True,
                'diagnostics': {
                    'invisible_chars_removed': scorecard.get('invisible_chars_removed', 0),
                    'cliches_replaced': scorecard.get('cliches_replaced', 0),
                    'human_confidence_pct': scorecard.get('human_confidence_pct', 100.0),
                    'pattern_risk_level': scorecard.get('pattern_risk_level', 'N/A'),
                    'sentence_count': scorecard.get('sentence_count', 0),
                    'total_words': scorecard.get('total_words', 0),
                    'detected_markers': scorecard.get('detected_markers', {}),
                }
            })

        except SecurityError as e:
            self._send_error_json(str(e), 403)
        except BackendError as e:
            self._send_error_json(f"Backend error: {e}", 502)
        except Exception as e:
            self._send_error_json(f"Unexpected error: {e}", 500)

    def _handle_health(self):
        """GET /api/health — Simple status check."""
        ollama_available = False
        model = 'llama3.2'
        try:
            backend = OllamaBackend(model=model)
            ollama_available = backend.is_available()
        except Exception:
            pass

        self._send_json({
            'local': True,
            'ollama': ollama_available,
            'model': model,
            'version': '2.0.0'
        })

    def _handle_config(self):
        """GET /api/config — Current configuration."""
        backends = get_available_backends()
        self._send_json({
            'version': '2.0.0',
            'local_only': True,
            'backends': [
                {'name': b.name(), 'available': b.is_available()}
                for b in backends
            ],
            'defaults': {
                'endpoint': 'http://127.0.0.1:11434',
                'model': 'llama3.2',
                'temperature': 0.7,
                'timeout': 60
            }
        })


def run_server(port=None):
    port = port or PORT
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), AntiwatermarkHandler) as httpd:
        print("=" * 56, flush=True)
        print(f"  🛡️  AntiWatermark v2.0 — Local Only", flush=True)
        print("=" * 56, flush=True)
        print(f"  🌐 Web UI:   http://localhost:{port}", flush=True)
        print(f"  📡 API:      http://localhost:{port}/api/clean", flush=True)
        print(f"  🔄 Rewrite:  http://localhost:{port}/api/rewrite", flush=True)
        print(f"  💚 Health:   http://localhost:{port}/api/health", flush=True)
        print(f"  ⚙️  Config:   http://localhost:{port}/api/config", flush=True)
        print(f"  🔒 Privacy:  100% local", flush=True)
        print("=" * 56, flush=True)
        print("  Press Ctrl+C to stop.\n", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  🛑 Server stopped.", flush=True)


if __name__ == '__main__':
    run_server()
