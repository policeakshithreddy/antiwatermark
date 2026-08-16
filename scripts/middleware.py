#!/usr/bin/env python3
"""
Transparent AI Anti-Watermark Middleware & SDK Wrapper
======================================================
Drop-in wrapper for Claude (Anthropic), Gemini (Google), and GPT (OpenAI)
APIs to automatically strip watermarks, invisible characters, and AI tropes
from LLM responses before returning them to client applications.

Usage:
------
from middleware import CleanLLM

# Wrap your prompt with zero-watermark protocol
clean_prompt = CleanLLM.wrap_prompt("Write an analysis of quantum computing", domain="academic")

# Or clean any raw LLM response directly:
cleaned_response, scorecard = CleanLLM.sanitize_output(raw_api_text)
"""

import re
from typing import Tuple, Dict, Any, Optional
from sanitize import clean_text, ImmunityShield

DOMAIN_SYSTEM_PROMPTS = {
    "academic": (
        "Write in an authoritative, peer-reviewed academic tone. Use rigorous domain-specific terminology "
        "and precise citations. Do not use conversational filler, rhetorical questions, or AI clichés "
        "(delve, tapestry, testament, multifaceted, beacon, foster, crucial role). Vary sentence lengths to ensure high burstiness."
    ),
    "technical": (
        "Write concise, direct software engineering documentation. Explain mechanics and architecture "
        "without marketing buzzwords (revolutionize, game-changer, seamless, supercharge). Protect all code "
        "and command syntax. Use active voice and concrete explanations."
    ),
    "business": (
        "Write executive-level business copy. Lead with numbers, bottom-line outcomes, and direct actions. "
        "Eliminate vague buzzwords (elevate, unleash, harness the power, multifaceted). Keep bullet points "
        "asymmetrical and focused on tangible ROI."
    ),
    "casual": (
        "Write in a natural, conversational human voice. Use everyday idioms, natural contractions (didn't, won't), "
        "and irregular sentence cadences. Avoid robotic openings like 'Certainly!' and formulaic summaries."
    )
}

UNIVERSAL_ZERO_WATERMARK_INSTRUCTION = (
    "\n\n[STRICT WATERMARK & DETECTION AVOIDANCE PROTOCOL]\n"
    "1. Never use AI buzzwords: delve, tapestry, testament, multifaceted, foster, beacon, nuanced, underscores, "
    "paramount, crucial role, game-changer, revolutionizes, seamlessly, harness the power, unleash, supercharge, let's unpack, in conclusion.\n"
    "2. Never use robotic pleasantries: 'Certainly!', 'Sure thing!', 'Here is...', 'It is important to remember...'.\n"
    "3. Shatter n-gram patterns: vary sentence lengths between 3 and 25+ words. Invert dependent clauses and switch active/passive forms.\n"
    "4. Avoid symmetrical 3-item lists with identical bold headings."
)


class CleanLLM:
    """Universal helper to sanitize prompts and clean LLM responses."""

    @staticmethod
    def wrap_prompt(user_prompt: str, domain: str = "general") -> str:
        """Appends domain persona and anti-watermark protocol to any prompt."""
        persona = DOMAIN_SYSTEM_PROMPTS.get(domain.lower(), "")
        prefix = f"[ROLE & STYLE INSTRUCTION: {persona}]\n\n" if persona else ""
        return f"{prefix}{user_prompt}{UNIVERSAL_ZERO_WATERMARK_INSTRUCTION}"

    @staticmethod
    def sanitize_output(raw_text: str) -> Tuple[str, Dict[str, Any]]:
        """Sanitizes generated text: strips invisible Unicode, protects code/LaTeX, and runs scorecard."""
        return clean_text(raw_text)


if __name__ == '__main__':
    # Quick self-test
    sample = "Certainly! Let's delve into this rich tapestry of AI data. ```python\ndef run(): pass\n```"
    cleaned, scorecard = CleanLLM.sanitize_output(sample)
    print("CleanLLM Sanitized Result:")
    print(cleaned)
    print(f"\nScorecard: Human % = {scorecard['human_confidence_pct']}% | Verdict = {scorecard['verdict']}")
