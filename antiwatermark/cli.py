import sys
import os
import json
import argparse
from .core import clean_text, rewrite_text, validate_output, ImmunityShield
from .backend import get_available_backends

def main():
    parser = argparse.ArgumentParser(
        prog="antiwatermark",
        description="Universal Text Cleaner, Steganography Stripper & Humanizer"
    )
    parser.add_argument("input", nargs="?", help="Text string or path to file to clean / analyze")
    parser.add_argument("-i", "--inplace", action="store_true", help="Modify file in-place")
    parser.add_argument("-j", "--json", action="store_true", help="Output diagnostic scorecard in JSON")
    parser.add_argument("-d", "--daemon", action="store_true", help="Run background clipboard sanitizer daemon")
    parser.add_argument("-w", "--web", action="store_true", help="Launch local interactive Web UI server")
    parser.add_argument("--backend", choices=['builtin', 'ollama', 'local-http'], default='builtin', help="Backend to use for rewriting")
    parser.add_argument("--validate", action="store_true", help="Strict validation mode for output")

    args = parser.parse_args()

    if args.daemon:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
        from scripts.clipboard_daemon import run_daemon
        run_daemon()
        return

    if args.web:
        import subprocess
        print("🌐 Launching antiwatermark Interactive Web UI...")
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app.py")])
        return

    if not args.input:
        parser.print_help()
        sys.exit(1)

    is_file = os.path.isfile(args.input)
    if is_file:
        with open(args.input, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    else:
        content = args.input

    if args.backend == 'builtin':
        cleaned, scorecard = clean_text(content)
    else:
        backends = get_available_backends()
        target = next((b for b in backends if args.backend in b.name()), None)
        if target:
            cleaned, scorecard = rewrite_text(content, backend=target)
        else:
            print(f"Backend '{args.backend}' not available, falling back to builtin.")
            cleaned, scorecard = clean_text(content)

    if args.validate:
        shield = ImmunityShield()
        shield.shield(content)
        validation = validate_output(content, cleaned, shield)
        if not validation.is_valid:
            print("Validation failed:", validation.failures)
            sys.exit(1)

    if is_file and args.inplace:
        with open(args.input, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        if not args.json:
            print(f"✅ Sanitized {args.input} in-place.")

    if args.json:
        scorecard['sanitized_text'] = cleaned
        print(json.dumps(scorecard, indent=2, ensure_ascii=False))
        return

    if not (is_file and args.inplace):
        print("=== SANITIZED TEXT ===")
        print(cleaned)

    # Print Scorecard
    sys.stderr.write("\n╔══════════════════════════════════════════════════════════════╗\n")
    sys.stderr.write("║           📊 ANTIWATERMARK HEURISTIC DIAGNOSTICS             ║\n")
    sys.stderr.write("╠══════════════════════════════════════════════════════════════╣\n")
    sys.stderr.write(f"║  Human Confidence Score : {scorecard['human_confidence_pct']}% (AI: {scorecard['ai_probability_pct']}%)\n")
    sys.stderr.write(f"║  Detection Verdict      : {scorecard['verdict']}\n")
    sys.stderr.write(f"║  Pattern Risk Level     : {scorecard.get('pattern_risk_level', 'Zero Risk')}\n")
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
