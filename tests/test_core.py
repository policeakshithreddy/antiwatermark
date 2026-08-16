"""
AntiWatermark Core Test Suite
==============================
Tests for deterministic sanitization, immunity shield, validation,
heuristic diagnostics, and idempotency.
"""

import pytest
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from antiwatermark.core import (
    clean_text,
    strip_invisible_characters,
    normalize_unicode,
    auto_humanize_prose,
    compute_heuristic_diagnostics,
    ImmunityShield,
    validate_output,
    ValidationResult,
    INVISIBLE_CODEPOINTS,
    INVISIBLE_REGEX,
)


class TestStripInvisibleCharacters:
    """Test zero-width and invisible character removal."""

    def test_removes_zero_width_space(self):
        text = "hello\u200Bworld"
        cleaned, count = strip_invisible_characters(text)
        assert cleaned == "helloworld"
        assert count == 1

    def test_removes_multiple_invisible_chars(self):
        text = "a\u200Bb\u200Cc\u200Dd\uFEFFe"
        cleaned, count = strip_invisible_characters(text)
        assert cleaned == "abcde"
        assert count == 4

    def test_removes_bom(self):
        text = "\uFEFFHello World"
        cleaned, count = strip_invisible_characters(text)
        assert cleaned == "Hello World"
        assert count == 1

    def test_removes_soft_hyphen(self):
        text = "anti\u00ADwatermark"
        cleaned, count = strip_invisible_characters(text)
        assert cleaned == "antiwatermark"
        assert count == 1

    def test_no_invisible_chars(self):
        text = "This is normal text."
        cleaned, count = strip_invisible_characters(text)
        assert cleaned == text
        assert count == 0

    def test_empty_input(self):
        cleaned, count = strip_invisible_characters("")
        assert cleaned == ""
        assert count == 0

    def test_all_invisible_chars(self):
        text = "\u200B\u200C\u200D\u200E\u200F"
        cleaned, count = strip_invisible_characters(text)
        assert cleaned == ""
        assert count == 5

    def test_korean_filler_chars(self):
        text = "test\u3164\uFFA0text"
        cleaned, count = strip_invisible_characters(text)
        assert cleaned == "testtext"
        assert count == 2

    def test_all_known_invisible_codepoints(self):
        """Every codepoint in our list should be stripped."""
        for cp in INVISIBLE_CODEPOINTS:
            text = f"before{cp}after"
            cleaned, count = strip_invisible_characters(text)
            assert cleaned == "beforeafter", f"Failed to strip codepoint U+{ord(cp):04X}"
            assert count == 1


class TestNormalizeUnicode:
    """Test Unicode NFKC normalization."""

    def test_normalizes_fullwidth(self):
        text = "\uff21\uff22\uff23"  # Ａ Ｂ Ｃ
        assert normalize_unicode(text) == "ABC"

    def test_normalizes_ligatures(self):
        text = "\ufb01"  # fi ligature
        assert normalize_unicode(text) == "fi"

    def test_normal_text_unchanged(self):
        text = "Hello World 123"
        assert normalize_unicode(text) == text


class TestImmunityShield:
    """Test code/math/URL protection from sanitization."""

    def test_shields_fenced_code_blocks(self):
        text = "before ```python\ndef foo():\n    pass\n``` after"
        shield = ImmunityShield()
        shielded = shield.shield(text)
        assert "```python" not in shielded
        assert "before" in shielded
        assert "after" in shielded
        unshielded = shield.unshield(shielded)
        assert unshielded == text

    def test_shields_inline_code(self):
        text = "Use `pip install antiwatermark` to install."
        shield = ImmunityShield()
        shielded = shield.shield(text)
        assert "`pip install antiwatermark`" not in shielded
        unshielded = shield.unshield(shielded)
        assert unshielded == text

    def test_shields_display_math(self):
        text = "The equation $$E = mc^2$$ is famous."
        shield = ImmunityShield()
        shielded = shield.shield(text)
        assert "$$E = mc^2$$" not in shielded
        unshielded = shield.unshield(shielded)
        assert unshielded == text

    def test_shields_inline_math(self):
        text = "We know that $x^2 + y^2 = z^2$ holds."
        shield = ImmunityShield()
        shielded = shield.shield(text)
        assert "$x^2 + y^2 = z^2$" not in shielded
        unshielded = shield.unshield(shielded)
        assert unshielded == text

    def test_shields_latex_brackets(self):
        text = "Consider \\[\\int_0^1 f(x) dx\\] in this context."
        shield = ImmunityShield()
        shielded = shield.shield(text)
        assert "\\int_0^1" not in shielded
        unshielded = shield.unshield(shielded)
        assert unshielded == text

    def test_shields_urls(self):
        text = "Visit https://github.com/example/repo for more."
        shield = ImmunityShield()
        shielded = shield.shield(text)
        assert "https://github.com/example/repo" not in shielded
        unshielded = shield.unshield(shielded)
        assert unshielded == text

    def test_shields_markdown_links(self):
        text = "See [AntiWatermark](https://github.com/repo) for details."
        shield = ImmunityShield()
        shielded = shield.shield(text)
        assert "[AntiWatermark](https://github.com/repo)" not in shielded
        unshielded = shield.unshield(shielded)
        assert unshielded == text

    def test_shields_email_addresses(self):
        text = "Contact user@example.com for support."
        shield = ImmunityShield()
        shielded = shield.shield(text)
        assert "user@example.com" not in shielded
        unshielded = shield.unshield(shielded)
        assert unshielded == text

    def test_placeholder_collision_safety(self):
        """Placeholders should never match natural text."""
        text = "The text __IMMUNE_BLOCK_0__ appears naturally here."
        shield = ImmunityShield()
        shielded = shield.shield(text)
        # Old format should not interfere
        unshielded = shield.unshield(shielded)
        assert "__IMMUNE_BLOCK_0__" in unshielded

    def test_multiple_blocks(self):
        text = "Use `code1` and `code2` with $$math$$ blocks."
        shield = ImmunityShield()
        shielded = shield.shield(text)
        assert "`code1`" not in shielded
        assert "`code2`" not in shielded
        assert "$$math$$" not in shielded
        unshielded = shield.unshield(shielded)
        assert unshielded == text

    def test_shield_validation(self):
        """Shield validate() should confirm all placeholders were restored."""
        text = "Use `code` and $$math$$ here."
        shield = ImmunityShield()
        shielded = shield.shield(text)
        unshielded = shield.unshield(shielded)
        assert shield.validate(unshielded)

    def test_shield_validation_fails_on_missing_placeholder(self):
        """validate() should fail if a placeholder remains in output."""
        text = "Use `code` here."
        shield = ImmunityShield()
        shielded = shield.shield(text)
        # Don't unshield — placeholders remain
        assert not shield.validate(shielded)


class TestAutoHumanizeProse:
    """Test AI cliché replacement."""

    def test_replaces_delve(self):
        text = "Let's delve into this topic."
        result, count = auto_humanize_prose(text)
        assert "delve" not in result.lower()
        assert count > 0

    def test_replaces_tapestry(self):
        text = "The rich tapestry of modern culture."
        result, count = auto_humanize_prose(text)
        assert "tapestry" not in result.lower()
        assert count > 0

    def test_replaces_certainly(self):
        text = "Certainly! Here is a breakdown of the issue."
        result, count = auto_humanize_prose(text)
        assert "Certainly" not in result
        assert count > 0

    def test_preserves_normal_text(self):
        text = "The cat sat on the mat. It was a good day."
        result, count = auto_humanize_prose(text)
        assert result.strip() == text.strip()
        assert count == 0

    def test_replaces_multiple_cliches(self):
        text = "Let's delve into this multifaceted topic. It is paramount to understand the nuanced approach."
        result, count = auto_humanize_prose(text)
        assert "delve" not in result.lower()
        assert "multifaceted" not in result.lower()
        assert "paramount" not in result.lower()
        assert "nuanced" not in result.lower()
        assert count >= 4

    def test_cleans_double_spaces(self):
        text = "Certainly! This  is   spaced."
        result, _ = auto_humanize_prose(text)
        assert "  " not in result


class TestCleanText:
    """Test the main clean_text pipeline."""

    def test_basic_cleaning(self):
        text = "Hello\u200B world\u200C!"
        cleaned, scorecard = clean_text(text)
        assert "\u200B" not in cleaned
        assert "\u200C" not in cleaned
        assert scorecard['invisible_chars_removed'] == 2

    def test_preserves_code_blocks(self):
        code = "```python\ndef delve():\n    pass\n```"
        text = f"Some text. {code} More text."
        cleaned, _ = clean_text(text)
        assert "```python\ndef delve():\n    pass\n```" in cleaned

    def test_preserves_inline_code(self):
        text = "Use `delve into` as a function name."
        cleaned, _ = clean_text(text)
        assert "`delve into`" in cleaned

    def test_preserves_math(self):
        text = "The equation $$E = mc^2$$ is fundamental."
        cleaned, _ = clean_text(text)
        assert "$$E = mc^2$$" in cleaned

    def test_preserves_urls(self):
        text = "Visit https://example.com/delve for more."
        cleaned, _ = clean_text(text)
        assert "https://example.com/delve" in cleaned

    def test_humanize_mode_replaces_cliches(self):
        text = "Let's delve into the multifaceted topic."
        cleaned, scorecard = clean_text(text, humanize=True)
        assert "delve" not in cleaned.lower()
        assert scorecard['cliches_replaced'] > 0

    def test_no_humanize_mode(self):
        text = "Let's delve into the multifaceted topic."
        cleaned, scorecard = clean_text(text, humanize=False)
        assert "delve" in cleaned.lower()
        assert scorecard['cliches_replaced'] == 0

    def test_idempotency(self):
        """clean_text(clean_text(x)) should produce the same result as clean_text(x)."""
        text = "Certainly! Let's delve into this rich tapestry of modern software."
        first_pass, _ = clean_text(text)
        second_pass, _ = clean_text(first_pass)
        assert first_pass == second_pass

    def test_empty_input(self):
        cleaned, scorecard = clean_text("")
        assert cleaned == ""

    def test_whitespace_only(self):
        cleaned, scorecard = clean_text("   \n\t  ")
        assert cleaned.strip() == ""

    def test_long_input(self):
        """Test with a large input to ensure no performance issues."""
        text = "This is a test sentence. " * 1000
        cleaned, scorecard = clean_text(text)
        assert len(cleaned) > 0

    def test_multilingual_text(self):
        text = "En conclusión, este es un texto importante."
        cleaned, scorecard = clean_text(text)
        assert len(cleaned) > 0

    def test_preserves_markdown_links(self):
        text = "See [project docs](https://example.com/delve) for info."
        cleaned, _ = clean_text(text)
        assert "https://example.com/delve" in cleaned
        assert "[project docs](https://example.com/delve)" in cleaned


class TestHeuristicDiagnostics:
    """Test the heuristic scoring system."""

    def test_empty_text(self):
        shield = ImmunityShield()
        result = compute_heuristic_diagnostics("", shield)
        assert result['human_confidence_pct'] == 100.0
        assert result['sentence_count'] == 0

    def test_natural_text_scores_high(self):
        text = (
            "I went to the store yesterday. "
            "The weather was surprisingly nice for this time of year. "
            "Got some milk, eggs, and bread. "
            "Then I ran into an old friend — hadn't seen her in ages."
        )
        shield = ImmunityShield()
        result = compute_heuristic_diagnostics(text, shield)
        assert result['human_confidence_pct'] >= 60.0

    def test_ai_heavy_text_scores_low(self):
        text = (
            "Let's delve into this multifaceted tapestry of innovation. "
            "It is important to note that this testament to human achievement "
            "underscores the paramount importance of fostering holistic growth. "
            "In conclusion, this beacon of progress revolutionizes our understanding."
        )
        shield = ImmunityShield()
        result = compute_heuristic_diagnostics(text, shield)
        assert result['human_confidence_pct'] < 50.0
        assert len(result['detected_markers']) > 0

    def test_scorecard_has_required_fields(self):
        shield = ImmunityShield()
        result = compute_heuristic_diagnostics("A sentence.", shield)
        required_fields = [
            'human_confidence_pct', 'ai_probability_pct', 'verdict',
            'sentence_count', 'total_words', 'avg_sentence_len',
            'std_dev_burstiness', 'burstiness_rating',
            'symmetrical_lists_detected', 'detected_markers',
            'pattern_risk_level'
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_no_synthid_in_labels(self):
        """Verify SynthID terminology has been removed from all outputs."""
        shield = ImmunityShield()
        result = compute_heuristic_diagnostics("Test text.", shield)
        # Should use 'pattern_risk_level' not 'synthid_risk_level'
        assert 'pattern_risk_level' in result
        assert 'synthid_risk_level' not in result


class TestValidation:
    """Test the validation layer."""

    def test_valid_output_passes(self):
        text = "Simple text with `code` and https://example.com"
        shield = ImmunityShield()
        shielded = shield.shield(text)
        processed = shield.unshield(shielded)
        result = validate_output(text, processed, shield)
        assert result.is_valid

    def test_url_modification_fails(self):
        original = "Visit https://example.com for more."
        processed = "Visit https://modified.com for more."
        shield = ImmunityShield()
        shield.shield(original)
        result = validate_output(original, processed, shield)
        assert not result.is_valid
        assert any("url" in f.lower() or "URL" in f for f in result.failures)

    def test_prompt_leakage_detected(self):
        original = "Write about cats."
        processed = "As an AI language model, I can write about cats."
        shield = ImmunityShield()
        shield.shield(original)
        result = validate_output(original, processed, shield)
        assert not result.is_valid
        assert any("leakage" in f.lower() or "prompt" in f.lower() for f in result.failures)

    def test_output_length_bounds(self):
        original = "Short text."
        processed = "Short text. " * 10000  # Way too long
        shield = ImmunityShield()
        shield.shield(original)
        result = validate_output(original, processed, shield, max_output_ratio=5.0)
        assert not result.is_valid


class TestEdgeCases:
    """Test edge cases and adversarial inputs."""

    def test_unicode_emoji(self):
        text = "Hello 🌍 World 🚀"
        cleaned, _ = clean_text(text)
        assert "🌍" in cleaned
        assert "🚀" in cleaned

    def test_cjk_text(self):
        text = "这是中文测试文本。日本語テスト。한국어 테스트."
        cleaned, _ = clean_text(text)
        assert "这是中文测试文本" in cleaned

    def test_mixed_invisible_and_visible(self):
        text = "a\u200Bb\u200Cc\u200Dd\u200Ee\u200Ff"
        cleaned, scorecard = clean_text(text)
        assert cleaned.startswith("abcdef") or "abcdef" in cleaned
        assert scorecard['invisible_chars_removed'] == 5

    def test_nested_code_blocks(self):
        text = "Outer ```python\ninner `code` here\n``` end"
        cleaned, _ = clean_text(text)
        assert "```python\ninner `code` here\n```" in cleaned

    def test_adjacent_protected_spans(self):
        text = "`a` `b` `c`"
        cleaned, _ = clean_text(text)
        assert "`a`" in cleaned
        assert "`b`" in cleaned
        assert "`c`" in cleaned

    def test_json_preservation(self):
        text = 'The config is ```json\n{"key": "delve"}\n``` here.'
        cleaned, _ = clean_text(text)
        assert '{"key": "delve"}' in cleaned
