"""
AntiWatermark API Test Suite
=============================
Tests for the HTTP API endpoints served by app.py.
Uses a test client to verify /api/clean, /api/rewrite, /api/health, /api/config.
"""

import pytest
import json
import sys
import os
import threading
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture(scope="module")
def server():
    """Start the AntiWatermark server in a background thread for testing."""
    from app import run_server
    import socketserver

    # Find a free port
    with socketserver.TCPServer(("", 0), None) as s:
        port = s.server_address[1]

    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()
    time.sleep(0.5)  # Give server time to start

    base_url = f"http://localhost:{port}"
    yield base_url


def _post(url, data):
    """Helper to POST JSON and get parsed response."""
    payload = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8')), resp.status


def _get(url):
    """Helper to GET and parse JSON response."""
    req = urllib.request.Request(url, method='GET')
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8')), resp.status


class TestHealthEndpoint:
    """GET /api/health"""

    def test_health_returns_ok(self, server):
        data, status = _get(f"{server}/api/health")
        assert status == 200
        assert data['local'] is True
        assert 'version' in data
        assert 'ollama' in data

    def test_health_has_model_field(self, server):
        data, _ = _get(f"{server}/api/health")
        assert 'model' in data


class TestConfigEndpoint:
    """GET /api/config"""

    def test_config_returns_ok(self, server):
        data, status = _get(f"{server}/api/config")
        assert status == 200
        assert data['local_only'] is True
        assert 'backends' in data
        assert 'defaults' in data

    def test_config_has_defaults(self, server):
        data, _ = _get(f"{server}/api/config")
        defaults = data['defaults']
        assert 'endpoint' in defaults
        assert 'model' in defaults
        assert 'temperature' in defaults
        assert 'timeout' in defaults

    def test_config_builtin_always_available(self, server):
        data, _ = _get(f"{server}/api/config")
        names = [b['name'] for b in data['backends']]
        assert 'builtin' in names


class TestCleanEndpoint:
    """POST /api/clean"""

    def test_clean_basic_text(self, server):
        data, status = _post(f"{server}/api/clean", {
            'text': 'Hello world.'
        })
        assert status == 200
        assert 'text' in data
        assert data['engine'] == 'builtin'
        assert data['validation_passed'] is True
        assert 'processing_time_ms' in data

    def test_clean_removes_cliches(self, server):
        data, _ = _post(f"{server}/api/clean", {
            'text': "Let's delve into this multifaceted topic."
        })
        assert 'delve' not in data['text'].lower()
        assert 'multifaceted' not in data['text'].lower()

    def test_clean_preserves_urls(self, server):
        data, _ = _post(f"{server}/api/clean", {
            'text': 'Visit https://example.com for more info.'
        })
        assert 'https://example.com' in data['text']

    def test_clean_preserves_code(self, server):
        data, _ = _post(f"{server}/api/clean", {
            'text': 'Use ```python\ndef delve(): pass\n``` here.'
        })
        assert 'def delve(): pass' in data['text']

    def test_clean_returns_diagnostics(self, server):
        data, _ = _post(f"{server}/api/clean", {
            'text': "Let's delve into things."
        })
        assert 'diagnostics' in data
        diag = data['diagnostics']
        assert 'invisible_chars_removed' in diag
        assert 'cliches_replaced' in diag
        assert 'human_confidence_pct' in diag

    def test_clean_strips_invisible_chars(self, server):
        data, _ = _post(f"{server}/api/clean", {
            'text': 'Hello\u200Bworld'
        })
        assert '\u200B' not in data['text']

    def test_clean_empty_text(self, server):
        data, status = _post(f"{server}/api/clean", {
            'text': ''
        })
        assert status == 200
        assert data['text'] == ''

    def test_clean_no_humanize(self, server):
        data, _ = _post(f"{server}/api/clean", {
            'text': "Let's delve into things.",
            'humanize': False
        })
        assert 'delve' in data['text'].lower()


class TestRewriteEndpoint:
    """POST /api/rewrite — Tests against Ollama (may skip if unavailable)."""

    def test_rewrite_without_ollama_returns_error(self, server):
        """If Ollama isn't running, should get 503 or backend error."""
        try:
            data, status = _post(f"{server}/api/rewrite", {
                'text': 'Hello world.'
            })
            # If Ollama IS running, this will succeed (status 200)
            # If not, we expect 503
            if status != 200:
                assert status in (502, 503)
        except urllib.error.HTTPError as e:
            assert e.code in (502, 503)

    def test_rewrite_empty_text_returns_error(self, server):
        """Empty text should return 400."""
        try:
            data, status = _post(f"{server}/api/rewrite", {
                'text': ''
            })
            assert status == 400
        except urllib.error.HTTPError as e:
            assert e.code == 400


class TestNotFoundEndpoint:
    """Unknown endpoints should return 404."""

    def test_unknown_post(self, server):
        try:
            _post(f"{server}/api/nonexistent", {'text': 'test'})
            assert False, "Should have raised"
        except urllib.error.HTTPError as e:
            assert e.code == 404

    def test_old_sanitize_endpoint_gone(self, server):
        """The old /api/sanitize endpoint should no longer exist."""
        try:
            _post(f"{server}/api/sanitize", {'text': 'test'})
            assert False, "Should have raised"
        except urllib.error.HTTPError as e:
            assert e.code == 404
