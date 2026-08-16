"""
AntiWatermark Backends Test Suite
==================================
Tests for LocalOnlyPolicy, backend interface, and builtin backend.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from antiwatermark.backend import (
    LocalOnlyPolicy,
    SecurityError,
    BackendError,
    BuiltinBackend,
    LocalHTTPBackend,
    OllamaBackend,
    RewriteConfig,
    get_available_backends,
)


class TestLocalOnlyPolicy:
    """Test that LocalOnlyPolicy enforces loopback-only endpoints."""

    def test_allows_localhost(self):
        assert LocalOnlyPolicy.validate_endpoint("http://localhost:8000/api")

    def test_allows_127_0_0_1(self):
        assert LocalOnlyPolicy.validate_endpoint("http://127.0.0.1:11434/v1/chat")

    def test_allows_ipv6_loopback(self):
        assert LocalOnlyPolicy.validate_endpoint("http://[::1]:8000/api")

    def test_allows_0_0_0_0(self):
        assert LocalOnlyPolicy.validate_endpoint("http://0.0.0.0:8000/api")

    def test_rejects_external_host(self):
        assert not LocalOnlyPolicy.validate_endpoint("https://api.openai.com/v1/chat")

    def test_rejects_arbitrary_domain(self):
        assert not LocalOnlyPolicy.validate_endpoint("https://example.com/api")

    def test_rejects_ip_address(self):
        assert not LocalOnlyPolicy.validate_endpoint("http://192.168.1.100:8000/api")

    def test_enforce_raises_on_remote(self):
        with pytest.raises(SecurityError):
            LocalOnlyPolicy.enforce("https://api.anthropic.com/v1/messages")

    def test_enforce_allows_localhost(self):
        # Should not raise
        LocalOnlyPolicy.enforce("http://localhost:11434/v1/chat/completions")

    def test_enforce_allows_loopback(self):
        LocalOnlyPolicy.enforce("http://127.0.0.1:8080/api")


class TestRewriteConfig:
    """Test RewriteConfig defaults and customization."""

    def test_defaults(self):
        config = RewriteConfig()
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.timeout_seconds == 30.0
        assert config.max_input_length == 50000
        assert config.domain == "general"

    def test_custom_config(self):
        config = RewriteConfig(
            temperature=0.3,
            max_tokens=2048,
            model="llama3.1",
            domain="academic",
            seed=42
        )
        assert config.temperature == 0.3
        assert config.model == "llama3.1"
        assert config.seed == 42


class TestBuiltinBackend:
    """Test the deterministic builtin backend."""

    def test_is_always_available(self):
        backend = BuiltinBackend()
        assert backend.is_available()

    def test_name(self):
        backend = BuiltinBackend()
        assert backend.name() == "builtin"

    def test_rewrite_returns_string(self):
        backend = BuiltinBackend()
        config = RewriteConfig()
        result = backend.rewrite("Hello world.", config)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_rewrite_removes_cliches(self):
        backend = BuiltinBackend()
        config = RewriteConfig()
        result = backend.rewrite("Let's delve into this multifaceted topic.", config)
        assert "delve" not in result.lower()


class TestLocalHTTPBackend:
    """Test LocalHTTPBackend initialization and policy enforcement."""

    def test_rejects_remote_endpoint(self):
        with pytest.raises(SecurityError):
            LocalHTTPBackend(endpoint="https://api.openai.com/v1/chat/completions")

    def test_accepts_localhost(self):
        # Should not raise
        backend = LocalHTTPBackend(
            endpoint="http://localhost:11434/v1/chat/completions",
            model="test-model"
        )
        assert "test-model" in backend.name()

    def test_is_available_returns_false_when_no_server(self):
        """When no local server is running, is_available should return False."""
        backend = LocalHTTPBackend(
            endpoint="http://localhost:59999/v1/chat/completions",
            model="test"
        )
        assert not backend.is_available()


class TestOllamaBackend:
    """Test OllamaBackend convenience adapter."""

    def test_default_endpoint(self):
        backend = OllamaBackend(model="llama3.2")
        assert "ollama" in backend.name()
        assert "llama3.2" in backend.name()

    def test_custom_host(self):
        backend = OllamaBackend(model="test", host="http://localhost:11434")
        assert backend.is_available() is not None  # returns bool

    def test_rejects_remote_host(self):
        with pytest.raises(SecurityError):
            OllamaBackend(model="test", host="https://remote-ollama.example.com")


class TestGetAvailableBackends:
    """Test backend discovery."""

    def test_always_includes_builtin(self):
        backends = get_available_backends()
        names = [b.name() for b in backends]
        assert "builtin" in names

    def test_returns_list(self):
        backends = get_available_backends()
        assert isinstance(backends, list)
        assert len(backends) >= 1
