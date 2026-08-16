"""
antiwatermark CLI Entry Point
=============================
"""

import sys
import os
import json
import argparse
from .core import clean_text


def main():
    parser = argparse.ArgumentParser(
        prog="antiwatermark",
        description="Universal AI Watermark Remover, Steganography Stripper & Detector Simulator"
    )
    parser.add_argument("input", nargs="?", help="Text string or path to file to dewatermark / analyze")
    parser.add_argument("-i", "--inplace", action="store_true", help="Modify file in-place")
    parser.add_argument("-j", "--json", action="store_true", help="Output diagnostic scorecard in JSON")
    parser.add_argument("-d", "--daemon", action="store_true", help="Run background clipboard sanitizer daemon")
    parser.add_argument("-w", "--web", action="store_true", help="Launch local interactive Web UI server")

    args = parser.parse_args()

    if args.daemon:
        from scripts.clipboard_daemon import run_daemon
        run_daemon()
        return

    if args.web:
        import subprocess
        print("🌐 Launching antiwatermark Interactive Web UI...")
        subprocess.run([sys.executable, "app.py"])
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

    cleaned, scorecard = clean_text(content)

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
