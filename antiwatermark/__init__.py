"""
antiwatermark - Universal AI Watermark Remover & Humanizer
"""

from .core import (
    clean_text,
    strip_invisible_characters,
    normalize_unicode,
    compute_ai_detector_scorecard,
    ImmunityShield,
    AI_BUZZWORDS_MULTILINGUAL
)
from .middleware import CleanLLM

__version__ = "1.0.0"
__all__ = [
    "clean_text",
    "strip_invisible_characters",
    "normalize_unicode",
    "compute_ai_detector_scorecard",
    "ImmunityShield",
    "AI_BUZZWORDS_MULTILINGUAL",
    "CleanLLM"
]
