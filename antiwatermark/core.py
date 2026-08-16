import uuid
import re
import unicodedata
import statistics
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field

INVISIBLE_CODEPOINTS = [
    '\u200B', '\u200C', '\u200D', '\u200E', '\u200F',
    '\u202A', '\u202B', '\u202C', '\u202D', '\u202E',
    '\u2060', '\u2061', '\u2062', '\u2063', '\u2064',
    '\u206A', '\u206B', '\u206C', '\u206D', '\u206E', '\u206F',
    '\uFEFF', '\u00AD', '\u180E', '\u034F',
    '\u115F', '\u1160', '\u3164', '\uFFA0'
]

INVISIBLE_REGEX = re.compile('[' + ''.join(re.escape(c) for c in INVISIBLE_CODEPOINTS) + ']')

LEXICAL_REPLACEMENTS = [
    (r'\bdelve(s|d|ing)? into\b', 'explore'),
    (r'\bdelve(s|d|ing)?\b', 'look closely at'),
    (r'\brich tapestry of\b', 'mix of'),
    (r'\btapestry of\b', 'blend of'),
    (r'\ba testament to\b', 'evidence of'),
    (r'\bstands as a testament to\b', 'shows the strength of'),
    (r'\bmultifaceted\b', 'complex'),
    (r'\bholistic\b', 'comprehensive'),
    (r'\bbeacon of\b', 'model for'),
    (r'\bfoster(ing)?\b', 'encouraging'),
    (r'\bnuanced\b', 'detailed'),
    (r'\bunderscores\b', 'highlights'),
    (r'\bpivotal\b', 'key'),
    (r'\bparamount\b', 'essential'),
    (r'\bplays a crucial role in\b', 'is key to'),
    (r'\bcrucial role\b', 'important role'),
    (r'\bcrucial\b', 'important'),
    (r'\bgame-changer\b', 'major upgrade'),
    (r'\brevolutioniz(e|es|ed|ing)\b', 'transforms'),
    (r'\bseamlessly\b', 'smoothly'),
    (r'\bintertwined\b', 'connected'),
    (r'\bharness(ing)? the power of\b', 'using'),
    (r'\bunleash(ing)?\b', 'deploying'),
    (r'\bsupercharge\b', 'speed up'),
    (r'\blet\'?s unpack\b', 'looking at'),
    (r'\bdive deep into\b', 'examine'),
    (r'\bdive into\b', 'explore'),
    (r'\bat its core\b', 'fundamentally'),
    (r'\bCertainly!?\s*', ''),
    (r'\bSure thing!?\s*', ''),
    (r'\bHere is a breakdown of\b', 'Regarding'),
    (r'\bHere\'?s a breakdown of\b', 'Regarding'),
    (r'\bIt is important to remember that\b', ''),
    (r'\bIt is worth noting that\b', ''),
    (r'\bKeep in mind that\b', ''),
    (r'\bIn conclusion,?\s*', 'Ultimately, '),
    (r'\bTo sum up,?\s*', 'In short, ')
]

AI_BUZZWORDS_MULTILINGUAL = {
    "English": [
        r'\bdelve(s|d|ing)?\b', r'\btapestry\b', r'\btestament\b', r'\bmultifaceted\b',
        r'\bholistic\b', r'\bbeacon\b', r'\bfoster(s|ed|ing)?\b', r'\bnuanced\b',
        r'\bunderscores?\b', r'\bpivotal\b', r'\bparamount\b', r'\bcrucial role\b',
        r'\bin conclusion\b', r'\bfurthermore\b', r'\bmoreover\b', r'\bintertwined\b',
        r'\bvibrant\b', r'\bresonates?\b', r'\bembark(s|ed|ing)?\b', r'\buncharted\b',
        r'\bgame-changer\b', r'\brevolutioniz(e|es|ed|ing)\b', r'\bculmination\b',
        r'\bseamlessly\b', r'\bcomprehensive guide\b', r'\blet\'?s dive in\b',
        r'\bcertainly!?\b', r'\bit is important to note\b', r'\bit is worth noting\b',
        r'\bplays a critical role\b', r'\bstands as a\b', r'\bshines a light\b',
        r'\bharness(ing)? the power\b', r'\belevat(e|es|ed|ing)\b', r'\bunleash(ing)?\b',
        r'\bsupercharge\b', r'\blet\'?s unpack\b', r'\beverything you need to know\b',
        r'\bdive deep\b', r'\bdive right in\b', r'\bat its core\b', r'\bgame changing\b',
        r'\bkeep in mind that\b', r'\bhere\'?s the breakdown\b', r'\bpowerhouse\b',
        r'\ba treasure trove\b', r'\bnavigating the\b', r'\bthe realm of\b',
        r'\ba myriad of\b', r'\ba plethora of\b', r'\bstands out as\b',
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

class ImmunityShield:
    def __init__(self):
        self.preserved_blocks: Dict[str, str] = {}
        
    def _generate_placeholder(self) -> str:
        short_id = uuid.uuid4().hex[:8]
        return f"⟦AW-{short_id}⟧"

    def shield(self, text: str) -> str:
        self.preserved_blocks.clear()

        def repl(match):
            placeholder = self._generate_placeholder()
            self.preserved_blocks[placeholder] = match.group(0)
            return placeholder

        # URLs
        text = re.sub(r'https?://[^\s<>"]+|www\.[^\s<>"]+', repl, text)
        # Markdown links
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', repl, text)
        # Email addresses
        text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', repl, text)
        # Code blocks
        text = re.sub(r'```[\s\S]*?```', repl, text)
        # LaTeX begin/end
        text = re.sub(r'\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\}', repl, text)
        # LaTeX math blocks
        text = re.sub(r'\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]', repl, text)
        # Inline math
        text = re.sub(r'(?<!\$)\$(?:[^\$\n]+)\$(?!\$)|\\\([\s\S]*?\\\)', repl, text)
        # Inline code
        text = re.sub(r'`[^`\n]+`', repl, text)

        return text

    def unshield(self, text: str) -> str:
        for placeholder, block in self.preserved_blocks.items():
            text = text.replace(placeholder, block)
        return text
        
    def validate(self, text: str) -> bool:
        """Check if all placeholders were successfully replaced."""
        return not any(p in text for p in self.preserved_blocks.keys())

def strip_invisible_characters(text: str) -> Tuple[str, int]:
    matches = len(INVISIBLE_REGEX.findall(text))
    cleaned = INVISIBLE_REGEX.sub('', text)
    return cleaned, matches

def normalize_unicode(text: str) -> str:
    return unicodedata.normalize('NFKC', text)

def auto_humanize_prose(text: str) -> Tuple[str, int]:
    replacements_made = 0
    modified_text = text
    for pattern, replacement in LEXICAL_REPLACEMENTS:
        matches = len(re.findall(pattern, modified_text, flags=re.IGNORECASE))
        if matches > 0:
            modified_text = re.sub(pattern, replacement, modified_text, flags=re.IGNORECASE)
            replacements_made += matches
    modified_text = re.sub(r'[ ]{2,}', ' ', modified_text)
    modified_text = re.sub(r'\n[ ]+', '\n', modified_text)
    return modified_text, replacements_made

def compute_heuristic_diagnostics(text: str, shield: ImmunityShield) -> Dict[str, Any]:
    shielded_text = shield.shield(text)
    raw_sentences = re.split(r'(?<=[.!?])\s+', shielded_text.strip())
    sentences = [s.strip() for s in raw_sentences if s.strip() and not s.startswith('⟦AW-')]

    if not sentences:
        return {
            'human_confidence_pct': 100.0,
            'ai_probability_pct': 0.0,
            'verdict': 'INSUFFICIENT PROSE TO EVALUATE',
            'sentence_count': 0,
            'total_words': 0,
            'avg_sentence_len': 0.0,
            'std_dev_burstiness': 0.0,
            'burstiness_rating': 'N/A',
            'symmetrical_lists_detected': False,
            'detected_markers': {},
            'pattern_risk_level': 'Zero Risk'
        }

    word_counts = [len(s.split()) for s in sentences]
    avg_len = sum(word_counts) / len(word_counts)
    std_dev = statistics.stdev(word_counts) if len(word_counts) > 1 else 0.0

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

    list_matches = re.findall(r'^\s*[-*•]\s+\*\*[^*]+\*\*:', text, flags=re.MULTILINE)
    has_symmetrical_triad = (len(list_matches) == 3)

    score = 100.0

    if std_dev < 3.5:
        score -= 35.0
    elif std_dev < 6.0:
        score -= 20.0
    elif std_dev < 8.0:
        score -= 5.0

    marker_penalty = min(total_marker_count * 12.0, 50.0)
    score -= marker_penalty

    if has_symmetrical_triad:
        score -= 15.0

    score = max(0.0, min(100.0, score))

    if score < 40:
        pattern_risk = "High Probability of Statistical Signature"
    elif score < 70:
        pattern_risk = "Moderate Pattern Match"
    else:
        pattern_risk = "Negligible (Shattered n-grams)"

    if score >= 80.0:
        verdict = "PASSED (Natural Human Cadence)"
    elif score >= 55.0:
        verdict = "SUSPICIOUS (Borderline AntiWatermark Heuristic)"
    else:
        verdict = "FLAGGED (High Probability AntiWatermark Heuristic Origin)"

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
        'pattern_risk_level': pattern_risk
    }

def clean_text(raw_text: str, humanize: bool = True) -> Tuple[str, Dict[str, Any]]:
    shield = ImmunityShield()
    shielded = shield.shield(raw_text)
    cleaned_shielded, invisible_count = strip_invisible_characters(shielded)
    cleaned_shielded = normalize_unicode(cleaned_shielded)
    
    cliches_replaced = 0
    if humanize:
        cleaned_shielded, cliches_replaced = auto_humanize_prose(cleaned_shielded)

    cleaned_shielded = re.sub(r'\r\n', '\n', cleaned_shielded)
    cleaned_shielded = re.sub(r'[\t ]+$', '', cleaned_shielded, flags=re.MULTILINE)
    final_cleaned = shield.unshield(cleaned_shielded)
    scorecard = compute_heuristic_diagnostics(final_cleaned, shield)
    scorecard['invisible_chars_removed'] = invisible_count
    scorecard['cliches_replaced'] = cliches_replaced

    return final_cleaned, scorecard

def rewrite_text(raw_text: str, backend=None, **kwargs) -> Tuple[str, Dict[str, Any]]:
    if backend is None:
        return clean_text(raw_text, humanize=True)
    
    shield = ImmunityShield()
    shielded = shield.shield(raw_text)
    
    # Delegated to backend
    from .backend import RewriteConfig
    config = RewriteConfig(**kwargs)
    rewritten_shielded = backend.rewrite(shielded, config)
    
    final_text = shield.unshield(rewritten_shielded)
    scorecard = compute_heuristic_diagnostics(final_text, shield)
    return final_text, scorecard

@dataclass
class ValidationResult:
    is_valid: bool
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

def validate_output(original: str, processed: str, shield: ImmunityShield, max_output_ratio: float = 3.0) -> ValidationResult:
    failures = []
    warnings = []
    
    # Check 1: Protected spans 100% exact match
    for placeholder, original_span in shield.preserved_blocks.items():
        if original_span not in processed:
            failures.append(f"Protected span missing or modified: {original_span[:20]}...")
            
    # Check 2: No leftover placeholders
    if not shield.validate(processed):
        failures.append("Orphaned placeholders found in output.")
    
    # Check 3: URL preservation
    original_urls = set(re.findall(r'https?://[^\s<>"]+', original))
    processed_urls = set(re.findall(r'https?://[^\s<>"]+', processed))
    missing_urls = original_urls - processed_urls
    if missing_urls:
        for url in missing_urls:
            failures.append(f"URL modified or missing: {url[:50]}")
        
    # Check 4: Output length bounds
    if not processed.strip() and original.strip():
        failures.append("Output is unexpectedly empty.")
    elif original.strip() and len(processed) > len(original) * max_output_ratio:
        failures.append("Output exceeds maximum allowed length expansion.")
        
    # Check 5: Prompt leakage
    leakage_patterns = [
        r"As an AI", r"I cannot", r"I'm sorry", r"I apologize",
        r"As a large language model"
    ]
    for pat in leakage_patterns:
        if re.search(pat, processed, re.IGNORECASE):
            failures.append(f"Prompt leakage detected: '{pat}'")

    return ValidationResult(
        is_valid=len(failures) == 0,
        failures=failures,
        warnings=warnings
    )
