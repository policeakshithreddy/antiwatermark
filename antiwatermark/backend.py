import urllib.parse
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Iterator

@dataclass
class RewriteConfig:
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout_seconds: float = 30.0
    max_input_length: int = 50000
    max_output_length: int = 60000
    seed: Optional[int] = None
    model: str = ""
    domain: str = "general"

class LocalOnlyPolicy:
    """Rejects non-loopback endpoints to ensure local-only operation."""
    ALLOWED_HOSTS = {'localhost', '127.0.0.1', '::1', '0.0.0.0'}
    
    @classmethod
    def validate_endpoint(cls, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname or ''
        return hostname in cls.ALLOWED_HOSTS
    
    @classmethod  
    def enforce(cls, url: str) -> None:
        if not cls.validate_endpoint(url):
            raise SecurityError(f"Endpoint '{url}' is not local. AntiWatermark only allows loopback addresses.")

class SecurityError(Exception):
    pass

class BackendError(Exception):
    pass

class BackendTimeoutError(BackendError):
    pass

class RewriterBackend(ABC):
    """Abstract base class for local rewrite backends."""
    
    @abstractmethod
    def name(self) -> str: ...
    
    @abstractmethod  
    def is_available(self) -> bool: ...
    
    @abstractmethod
    def rewrite(self, text: str, config: RewriteConfig) -> str: ...
    
    def stream(self, text: str, config: RewriteConfig) -> Iterator[str]:
        yield self.rewrite(text, config)

class BuiltinBackend(RewriterBackend):
    """Deterministic heuristic backend — always available, no model needed."""
    def name(self): return "builtin"
    def is_available(self): return True
    def rewrite(self, text, config):
        from .core import clean_text
        cleaned, _ = clean_text(text, humanize=True)
        return cleaned

class LocalHTTPBackend(RewriterBackend):
    """OpenAI-compatible localhost HTTP backend (works with llama.cpp, Ollama, LM Studio, etc.)"""
    def __init__(self, endpoint='http://localhost:11434/v1/chat/completions', model='llama3.2'):
        LocalOnlyPolicy.enforce(endpoint)
        self.endpoint = endpoint
        self.model = model
    
    def name(self): return f"local-http ({self.model})"
    
    def is_available(self):
        import urllib.request
        try:
            # Just check if the server responds
            parsed = urllib.parse.urlparse(self.endpoint)
            health_url = f"{parsed.scheme}://{parsed.netloc}/"
            req = urllib.request.Request(health_url, method='GET')
            urllib.request.urlopen(req, timeout=3)
            return True
        except Exception:
            return False
    
    def rewrite(self, text, config):
        import json, urllib.request
        from .middleware import CleanLLM
        
        prompt = CleanLLM.wrap_prompt(text, domain=config.domain)
        payload = {
            'model': config.model or self.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': config.temperature,
            'max_tokens': config.max_tokens,
        }
        if config.seed is not None:
            payload['seed'] = config.seed
        
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=config.timeout_seconds) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
        except Exception as e:
            raise BackendError(f"Local HTTP backend error: {e}")

class OllamaBackend(LocalHTTPBackend):
    """Convenience adapter for Ollama."""
    def __init__(self, model='llama3.2', host='http://localhost:11434'):
        super().__init__(endpoint=f"{host}/v1/chat/completions", model=model)
    
    def name(self): return f"ollama ({self.model})"

def get_available_backends():
    backends = [BuiltinBackend()]
    try:
        ollama = OllamaBackend()
        if ollama.is_available():
            backends.append(ollama)
    except SecurityError:
        pass
    return backends
