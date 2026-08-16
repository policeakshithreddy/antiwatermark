"""
antiwatermark - Universal Text Cleaner & Humanizer
"""

from .core import (
    clean_text,
    strip_invisible_characters,
    normalize_unicode,
    compute_heuristic_diagnostics,
    ImmunityShield,
    AI_BUZZWORDS_MULTILINGUAL,
    ValidationResult,
    validate_output
)
from .middleware import CleanLLM
from .backend import (
    RewriterBackend,
    LocalHTTPBackend,
    OllamaBackend,
    BuiltinBackend,
    LocalOnlyPolicy
)

__version__ = "2.0.0"
__all__ = [
    "clean_text",
    "strip_invisible_characters",
    "normalize_unicode",
    "compute_heuristic_diagnostics",
    "ImmunityShield",
    "AI_BUZZWORDS_MULTILINGUAL",
    "CleanLLM",
    "RewriterBackend",
    "LocalHTTPBackend",
    "OllamaBackend",
    "BuiltinBackend",
    "LocalOnlyPolicy",
    "ValidationResult",
    "validate_output"
]
