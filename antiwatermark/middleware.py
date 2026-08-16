from typing import Tuple, Dict, Any
from .core import clean_text

DOMAIN_SYSTEM_PROMPTS = {
    "academic": (
        "Write in an authoritative, peer-reviewed academic tone. Use rigorous domain-specific terminology "
        "and precise citations. Do not use conversational filler or rhetorical questions."
    ),
    "technical": (
        "Write concise, direct software engineering documentation. Explain mechanics and architecture "
        "clearly. Use active voice and concrete explanations."
    ),
    "business": (
        "Write executive-level business copy. Lead with numbers, bottom-line outcomes, and direct actions. "
        "Keep bullet points focused on tangible ROI."
    ),
    "casual": (
        "Write in a natural, conversational human voice. Use everyday idioms, natural contractions, "
        "and irregular sentence cadences."
    )
}

UNIVERSAL_REWRITE_INSTRUCTION = (
    "\n\n[EDITING CONTRACT]\n"
    "1. Preserve factual meaning, named entities, numbers, citations, URLs, protected spans.\n"
    "2. Improve clarity and naturalness.\n"
    "3. Do NOT add facts absent from source.\n"
    "4. Do NOT summarize unless explicitly requested.\n"
    "5. Do NOT alter code, math, URLs, or any placeholders like ⟦AW-...⟧.\n"
    "6. Return ONLY the rewritten text without any preamble, acknowledgement, or explanation."
)

class CleanLLM:
    """Universal helper to sanitize prompts and clean LLM responses."""

    @staticmethod
    def wrap_prompt(user_prompt: str, domain: str = "general") -> str:
        persona = DOMAIN_SYSTEM_PROMPTS.get(domain.lower(), "")
        prefix = f"[ROLE & STYLE INSTRUCTION: {persona}]\n\n" if persona else ""
        return f"{prefix}{user_prompt}{UNIVERSAL_REWRITE_INSTRUCTION}"

    @staticmethod
    def sanitize_output(raw_text: str) -> Tuple[str, Dict[str, Any]]:
        return clean_text(raw_text)
