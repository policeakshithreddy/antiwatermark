#!/usr/bin/env python3
"""
AI Clipboard Watermark Sanitizer Daemon
=======================================
Runs in the background and automatically cleans text whenever you copy (Cmd+C / Ctrl+C)
from Claude.ai, Gemini, ChatGPT, or web portals.

Automatically strips:
- Zero-width spaces, joiners, non-joiners, BOM, and hidden Unicode watermarks.
- Normalizes Unicode homoglyphs (NFKC).
- Strips trailing formatting and hidden metadata before pasting into Word/Docs/Slack.
"""

import time
import subprocess
import sys
import os

# Import the core sanitization engine
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from antiwatermark.core import clean_text, strip_invisible_characters, normalize_unicode


def get_clipboard() -> str:
    """Gets current clipboard text across macOS, Linux, and Windows."""
    try:
        # macOS
        if sys.platform == 'darwin':
            p = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, _ = p.communicate()
            return out.decode('utf-8', errors='ignore')
        # Linux (xclip / wl-paste)
        elif sys.platform.startswith('linux'):
            try:
                p = subprocess.Popen(['wl-paste'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, _ = p.communicate()
                return out.decode('utf-8', errors='ignore')
            except FileNotFoundError:
                p = subprocess.Popen(['xclip', '-selection', 'clipboard', '-o'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, _ = p.communicate()
                return out.decode('utf-8', errors='ignore')
        # Windows
        elif sys.platform == 'win32':
            import win32clipboard
            win32clipboard.OpenClipboard()
            data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            return data
    except Exception:
        pass
    return ""


def set_clipboard(text: str):
    """Sets clipboard text across macOS, Linux, and Windows."""
    try:
        if sys.platform == 'darwin':
            p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            p.communicate(text.encode('utf-8'))
        elif sys.platform.startswith('linux'):
            try:
                p = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE)
                p.communicate(text.encode('utf-8'))
            except FileNotFoundError:
                p = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
                p.communicate(text.encode('utf-8'))
        elif sys.platform == 'win32':
            import win32clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text)
            win32clipboard.CloseClipboard()
    except Exception:
        pass


def run_daemon(poll_interval: float = 0.5):
    print("==============================================================")
    print("📋 AI Clipboard Watermark Sanitizer Daemon is RUNNING...")
    print("==============================================================")
    print("• Monitoring clipboard for Claude, Gemini & ChatGPT copied text.")
    print("• Automatically stripping invisible characters & homoglyphs in real-time.")
    print("• Press Ctrl+C at any time to stop.\n")

    last_clipboard = get_clipboard()

    try:
        while True:
            time.sleep(poll_interval)
            current_clipboard = get_clipboard()

            if current_clipboard and current_clipboard != last_clipboard:
                # Process the newly copied text
                cleaned, scorecard = clean_text(current_clipboard)

                # If invisible characters were found or text was modified
                if scorecard['invisible_chars_removed'] > 0:
                    set_clipboard(cleaned)
                    last_clipboard = cleaned
                    print(f"[{time.strftime('%X')}] 🧹 Cleaned {scorecard['invisible_chars_removed']} invisible characters from clipboard!")
                    print(f"            Human Score: {scorecard['human_confidence_pct']}% | Verdict: {scorecard['verdict']}")
                else:
                    last_clipboard = current_clipboard
                    if scorecard['human_confidence_pct'] < 60.0 and len(current_clipboard.split()) > 10:
                        print(f"[{time.strftime('%X')}] ⚠️ Copied text contains AI Markers: {scorecard['detected_markers']}")
                        print(f"            Human Score: {scorecard['human_confidence_pct']}% (Tip: Run through SKILL.md dewatermarking)")
    except KeyboardInterrupt:
        print("\n🛑 Clipboard Sanitizer Daemon stopped.")


if __name__ == '__main__':
    run_daemon()
