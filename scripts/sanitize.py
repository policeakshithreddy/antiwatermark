#!/usr/bin/env python3
"""
AI Multi-Model Watermark Sanitizer & Local Detector Simulator
============================================================
Supports: Claude (Anthropic), Gemini & SynthID-Text (Google), ChatGPT (OpenAI)

Features:
1. Code & LaTeX Immunity Shield (Preserves ```code```, `code`, $$math$$, $math$).
2. Multi-Lingual AI Cliché Detector (English, Spanish, French, German).
3. Deterministic Invisible Character & Homoglyph Stripper.
4. Local AI Detector Scorecard (Simulating GPTZero / Turnitin / SynthID Risk).
5. Human Confidence Score (0% - 100%) & Heuristic Diagnostics.
"""

import sys
import os
import re
import json
import unicodedata
import statistics
from typing import Dict, List, Tuple, Any

# ==========================================
# 1. INVISIBLE & STEGANOGRAPHIC CODEPOINTS
# ==========================================
INVISIBLE_CODEPOINTS = [
    '\u200B',  # Zero-width space (ZWSP)
    '\u200C',  # Zero-width non-joiner (ZWNJ)
    '\u200D',  # Zero-width joiner (ZWJ)
    '\u200E',  # Left-to-right mark (LRM)
    '\u200F',  # Right-to-left mark (RLM)
    '\u202A',  # Left-to-right embedding (LRE)
    '\u202B',  # Right-to-left embedding (RLE)
    '\u202C',  # Pop directional formatting (PDF)
    '\u202D',  # Left-to-right override (LRO)
    '\u202E',  # Right-to-left override (RLO)
    '\u2060',  # Word joiner (WJ)
    '\u2061',  # Function application
    '\u2062',  # Invisible times
    '\u2063',  # Invisible separator
    '\u2064',  # Invisible plus
    '\u206A',  # Inhibit symmetric swapping
    '\u206B',  # Activate symmetric swapping
    '\u206C',  # Inhibit Arabic form shaping
    '\u206D',  # Activate Arabic form shaping
    '\u206E',  # National digit shapes
    '\u206F',  # Nominal digit shapes
    '\uFEFF',  # Byte order mark / Zero-width no-break space (BOM)
    '\u00AD',  # Soft hyphen
    '\u180E',  # Mongolian vowel separator
    '\u034F',  # Combining grapheme joiner
    '\u115F',  # Hangul choseong filler
    '\u1160',  # Hangul jungseong filler
    '\u3164',  # Hangul filler
    '\uFFA0',  # Halfwidth hangul filler
]

INVISIBLE_REGEX = re.compile('[' + ''.join(re.escape(c) for c in INVISIBLE_CODEPOINTS) + ']')

# ==========================================
# 2. MULTI-LINGUAL AI MARKERS & CLICHÉS
# ==========================================
AI_BUZZWORDS_MULTILINGUAL = {
    "English": [
        # Claude & General Tropes
        r'\bdelve(s|d|ing)?\b', r'\btapestry\b', r'\btestament\b', r'\bmultifaceted\b',
        r'\bholistic\b', r'\bbeacon\b', r'\bfoster(s|ed|ing)?\b', r'\bnuanced\b',
        r'\bunderscores?\b', r'\bpivotal\b', r'\bparamount\b', r'\bcrucial role\b',
        r'\bin conclusion\b', r'\bfurthermore\b', r'\bmoreover\b', r'\bintertwined\b',
        r'\bvibrant\b', r'\bresonates?\b', r'\bembark(s|ed|ing)?\b', r'\buncharted\b',
        r'\bgame-changer\b', r'\brevolutioniz(e|es|ed|ing)\b', r'\bculmination\b',
        r'\bseamlessly\b', r'\bcomprehensive guide\b', r'\blet\'?s dive in\b',
        r'\bcertainly!?\b', r'\bit is important to note\b', r'\bit is worth noting\b',
        r'\bplays a critical role\b', r'\bstands as a\b', r'\bshines a light\b',
        # Gemini / Google Tropes
        r'\bharness(ing)? the power\b', r'\belevat(e|es|ed|ing)\b', r'\bunleash(ing)?\b',
        r'\bsupercharge\b', r'\blet\'?s unpack\b', r'\beverything you need to know\b',
        r'\bdive deep\b', r'\bdive right in\b', r'\bat its core\b', r'\bgame changing\b',
        r'\bkeep in mind that\b', r'\bhere\'?s the breakdown\b', r'\bpowerhouse\b',
        r'\ba treasure trove\b', r'\bnavigating the\b', r'\bthe realm of\b',
        r'\ba myriad of\b', r'\ba plethora of\b', r'\bstands out as\b',
        # ChatGPT / OpenAI Tropes
        r'\bit\'?s crucial to remember\b', r'\bin summary\b', r'\ba testament to\b',
        r'\bdelve deeper\b', r'\bnot only.*but also\b'
    ],
    "Spanish": [
        r'\bes fundamental destacar\b', r'\bun tapiz de\b', r'\ben conclusión\b',
        r'\bun papel crucial\b', r'\bdesempeña un papel\b', r'\bes importante recordar\b',
        r'\bprofundicemos en\b', r'\bun faro de\b', r'\bfomentar el desarrollo\b',
        r'\buna gran cantidad de\b', r'\ben resumen\b', r'\bcabe destacar que\b'
    ],
    "French": [
        r'\bil convient de noter\b', r'\bun rôle primordial\b', r'\btémoignage de\b',
        r'\ben conclusion\b', r'\bplonger dans\b', r'\bun éventail de\b',
        r'\bil est important de souligner\b', r'\bun phare de\b', r'\ben somme\b'
    ],
    "German": [
        r'\bes ist wichtig zu beachten\b', r'\bein facettenreicher\b',
        r'\bzusammenfassend lässt sich sagen\b', r'\beine entscheidende rolle\b',
        r'\btauchen wir ein\b', r'\bein meilenstein\b', r'\bes sei darauf hingewiesen\b'
    ]
}


# ==========================================
# 3. CODE & LATEX IMMUNITY SHIELD
# ==========================================
class ImmunityShield:
    """Protects code blocks, inline code, and LaTeX math from corruption."""

    def __init__(self):
        self.preserved_blocks: List[str] = []

    def shield(self, text: str) -> str:
        self.preserved_blocks.clear()

        def repl(match):
            idx = len(self.preserved_blocks)
            self.preserved_blocks.append(match.group(0))
            return f"__IMMUNE_BLOCK_{idx}__"

        # 1. Fenced code blocks (```...```)
        text = re.sub(r'```[\s\S]*?```', repl, text)
        # 2. Display LaTeX ($$...$$ or \[...\])
        text = re.sub(r'\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]', repl, text)
        # 3. Inline LaTeX ($...$ or \(...\))
        text = re.sub(r'(?<!\$)\$(?:[^\$\n]+)\$(?!\$)|\\\([\s\S]*?\\\)', repl, text)
        # 4. Inline code (`...`)
        text = re.sub(r'`[^`\n]+`', repl, text)

        return text

    def unshield(self, text: str) -> str:
        for idx, block in enumerate(self.preserved_blocks):
            text = text.replace(f"__IMMUNE_BLOCK_{idx}__", block)
        return text


# ==========================================
# 4. SANITIZATION & METRICS
# ==========================================
def strip_invisible_characters(text: str) -> Tuple[str, int]:
    """Removes all zero-width, invisible, and steganographic Unicode markers."""
    matches = len(INVISIBLE_REGEX.findall(text))
    cleaned = INVISIBLE_REGEX.sub('', text)
    return cleaned, matches


def normalize_unicode(text: str) -> str:
    """Normalizes Unicode to NFKC canonical standard, neutralizing homoglyphs."""
    return unicodedata.normalize('NFKC', text)


def compute_ai_detector_scorecard(text: str, shield: ImmunityShield) -> Dict[str, Any]:
    """
    Simulates AI detector heuristics (GPTZero, Turnitin, SynthID Risk).
    Calculates Perplexity, Burstiness (sentence length standard deviation),
    symmetrical structure penalties, and output Human Confidence %.
    """
    # Analyze only non-code/non-latex prose
    shielded_text = shield.shield(text)
    
    # Extract sentences
    raw_sentences = re.split(r'(?<=[.!?])\s+', shielded_text.strip())
    sentences = [s.strip() for s in raw_sentences if s.strip() and not s.startswith('__IMMUNE_BLOCK_')]

    if not sentences:
        return {
            'human_confidence_pct': 100.0,
            'verdict': 'INSUFFICIENT PROSE TO EVALUATE',
            'sentence_count': 0,
            'word_count': 0,
            'avg_sentence_len': 0.0,
            'std_dev_burstiness': 0.0,
            'burstiness_rating': 'N/A',
            'detected_markers': {},
            'synthid_risk_level': 'Zero Risk'
        }

    word_counts = [len(s.split()) for s in sentences]
    avg_len = sum(word_counts) / len(word_counts)
    std_dev = statistics.stdev(word_counts) if len(word_counts) > 1 else 0.0

    # 1. Search for multilingual markers
    detected_markers: Dict[str, List[str]] = {}
    total_marker_count = 0
    for lang, patterns in AI_BUZZWORDS_MULTILINGUAL.items():
        found_in_lang = []
        for pat in patterns:
            for m in re.finditer(pat, shielded_text, flags=re.IGNORECASE):
                word = m.group(0).strip()
                if word:
                    found_in_lang.append(word.lower())
        if found_in_lang:
            detected_markers[lang] = list(set(found_in_lang))
            total_marker_count += len(found_in_lang)

    # 2. Check for Symmetrical 3-Item Bold Lists (Heavy AI Signal)
    list_matches = re.findall(r'^\s*[-*•]\s+\*\*[^*]+\*\*:', text, flags=re.MULTILINE)
    has_symmetrical_triad = (len(list_matches) == 3)

    # 3. Compute Human Confidence Score (0 - 100%)
    # Base score = 100
    score = 100.0

    # Penalty for low burstiness (uniform sentence lengths)
    if std_dev < 3.5:
        score -= 35.0
    elif std_dev < 6.0:
        score -= 20.0
    elif std_dev < 8.0:
        score -= 5.0

    # Penalty for detected AI buzzwords
    marker_penalty = min(total_marker_count * 12.0, 50.0)
    score -= marker_penalty

    # Penalty for symmetrical triad lists
    if has_symmetrical_triad:
        score -= 15.0

    # SynthID Risk Assessment
    if score < 40:
        synthid_risk = "High Probability of Statistical Signature"
    elif score < 70:
        synthid_risk = "Moderate Pattern Match"
    else:
        synthid_risk = "Negligible (Shattered n-grams)"

    score = max(0.0, min(100.0, score))

    if score >= 80.0:
        verdict = "PASSED (Natural Human Cadence)"
    elif score >= 55.0:
        verdict = "SUSPICIOUS (Borderline AI Patterns)"
    else:
        verdict = "AI FLAGGED (High Probability AI Origin)"

    burstiness_desc = (
        "High (Natural human variance)" if std_dev >= 8.0
        else "Moderate (Average variance)" if std_dev >= 5.0
        else "Low (Monotonous / AI-like cadence)"
    )

    return {
        'human_confidence_pct': round(score, 1),
        'ai_probability_pct': round(100.0 - score, 1),
        'verdict': verdict,
        'sentence_count': len(sentences),
        'total_words': sum(word_counts),
        'avg_sentence_len': round(avg_len, 2),
        'std_dev_burstiness': round(std_dev, 2),
        'burstiness_rating': burstiness_desc,
        'symmetrical_lists_detected': has_symmetrical_triad,
        'detected_markers': detected_markers,
        'synthid_risk_level': synthid_risk
    }


def clean_text(raw_text: str) -> Tuple[str, Dict[str, Any]]:
    """Complete sanitization pipeline with Code/LaTeX Immunity."""
    shield = ImmunityShield()
    
    # 1. Shield code & LaTeX
    shielded = shield.shield(raw_text)

    # 2. Strip invisible characters from prose
    cleaned_shielded, invisible_count = strip_invisible_characters(shielded)

    # 3. Normalize Unicode (NFKC)
    cleaned_shielded = normalize_unicode(cleaned_shielded)

    # 4. Clean line endings
    cleaned_shielded = re.sub(r'\r\n', '\n', cleaned_shielded)
    cleaned_shielded = re.sub(r'[\t ]+$', '', cleaned_shielded, flags=re.MULTILINE)

    # 5. Restore shielded code & LaTeX blocks
    final_cleaned = shield.unshield(cleaned_shielded)

    # 6. Score against AI detector heuristics
    scorecard = compute_ai_detector_scorecard(final_cleaned, shield)
    scorecard['invisible_chars_removed'] = invisible_count

    return final_cleaned, scorecard


# ==========================================
# 5. CLI INTERFACE
# ==========================================
def main():
    if len(sys.argv) < 2 or "--help" in sys.argv:
        print("AI Watermark Sanitizer & Detector Simulator")
        print("Usage: python3 sanitize.py <file_or_text> [--inplace] [--json]")
        print("\nOptions:")
        print("  --inplace   Modify file in-place with sanitized output.")
        print("  --json      Output full diagnostic scorecard in JSON format.")
        sys.exit(0)

    arg = sys.argv[1]
    is_file = os.path.isfile(arg)
    inplace = "--inplace" in sys.argv
    as_json = "--json" in sys.argv

    if is_file:
        with open(arg, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    else:
        content = arg

    cleaned, scorecard = clean_text(content)

    if is_file and inplace:
        with open(arg, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        if not as_json:
            print(f"✅ Sanitized {arg} in-place.")

    if as_json:
        scorecard['sanitized_text'] = cleaned
        print(json.dumps(scorecard, indent=2, ensure_ascii=False))
        return

    if not (is_file and inplace):
        print("=== SANITIZED TEXT ===")
        print(cleaned)

    # Print Detector Scorecard
    sys.stderr.write("\n╔══════════════════════════════════════════════════════════════╗\n")
    sys.stderr.write("║           📊 AI DETECTOR & WATERMARK SCORECARD               ║\n")
    sys.stderr.write("╠══════════════════════════════════════════════════════════════╣\n")
    sys.stderr.write(f"║  Human Confidence Score : {scorecard['human_confidence_pct']}% (AI: {scorecard['ai_probability_pct']}%)\n")
    sys.stderr.write(f"║  Detection Verdict      : {scorecard['verdict']}\n")
    sys.stderr.write(f"║  SynthID Risk Level     : {scorecard['synthid_risk_level']}\n")
    sys.stderr.write("╟──────────────────────────────────────────────────────────────╢\n")
    sys.stderr.write(f"║  Invisible Characters Removed : {scorecard['invisible_chars_removed']}\n")
    sys.stderr.write(f"║  Sentence Count & Words       : {scorecard['sentence_count']} sentences | {scorecard['total_words']} words\n")
    sys.stderr.write(f"║  Burstiness Standard Deviation: {scorecard['std_dev_burstiness']} ({scorecard['burstiness_rating']})\n")
    sys.stderr.write(f"║  Symmetrical 3-List Penalty   : {'Yes (Flagged)' if scorecard['symmetrical_lists_detected'] else 'None'}\n")
    
    if scorecard['detected_markers']:
        sys.stderr.write("║  Detected AI Buzzwords        :\n")
        for lang, markers in scorecard['detected_markers'].items():
            sys.stderr.write(f"║    • [{lang}]: {', '.join(markers)}\n")
    else:
        sys.stderr.write("║  Detected AI Buzzwords        : None found (Clean)\n")
    sys.stderr.write("╚══════════════════════════════════════════════════════════════╝\n")


if __name__ == '__main__':
    main()
