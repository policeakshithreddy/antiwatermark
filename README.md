# AntiWatermark

**Local-only AI text watermark remover, steganography stripper, and humanizer.**

Strips invisible Unicode markers, replaces AI clichés, validates output integrity, and optionally rewrites text via a local AI model. No cloud services. No API keys. No data leaves your machine.

🔒 **100% Local — No Data Leaves Your Machine**

---

## Quick Start

```bash
git clone https://github.com/policeakshithreddy/antiwatermark
cd antiwatermark

python -m venv .venv
source .venv/bin/activate

pip install -e .

pytest

python app.py
```

Open **http://localhost:8000**

This works without any AI model. Fast Mode is always available.

---

## Two Modes

### Fast Clean (Default)

Deterministic, instant, zero dependencies.

- Strips 26+ invisible Unicode characters (zero-width spaces, BOM, soft hyphens, etc.)
- Replaces 30+ AI clichés ("delve into", "rich tapestry", "multifaceted", "Certainly!")
- Protects code blocks, inline code, LaTeX, URLs, Markdown links, and emails
- Validates output integrity
- Runs heuristic diagnostics

### Local Neural (Optional)

Uses a local AI model via [Ollama](https://ollama.com) for deeper text rewriting.

```bash
# Install Ollama (https://ollama.com)
ollama pull llama3.2
ollama serve

# Then select "Local Neural" in the UI
```

No cloud APIs. No API keys. Ollama runs entirely on your machine.

---

## Installation

**Base (Fast Mode only):**

```bash
pip install -e .
```

**With neural support:**

```bash
pip install -e ".[neural]"
```

---

## Usage

### Web UI

```bash
python app.py
# Open http://localhost:8000
```

### CLI

```bash
# Clean text
antiwatermark "Your AI-generated text here"

# Clean a file in-place
antiwatermark document.txt --inplace

# Output diagnostics as JSON
antiwatermark "text" --json

# Use Ollama backend
antiwatermark "text" --backend ollama

# Launch Web UI
antiwatermark --web

# Run clipboard daemon
antiwatermark --daemon
```

### Python API

```python
from antiwatermark import clean_text, validate_output, ImmunityShield

# Fast clean
cleaned, diagnostics = clean_text("Your AI text here")
print(cleaned)
print(f"Human confidence: {diagnostics['human_confidence_pct']}%")

# With validation
shield = ImmunityShield()
shield.shield(original_text)
result = validate_output(original_text, processed_text, shield)
if result.is_valid:
    print("Output validated successfully")
else:
    print(f"Validation failed: {result.failures}")
```

### REST API

```bash
# Health check
curl http://localhost:8000/api/health

# Fast clean
curl -X POST http://localhost:8000/api/clean \
  -H 'Content-Type: application/json' \
  -d '{"text": "Your text here"}'

# Neural rewrite (requires Ollama)
curl -X POST http://localhost:8000/api/rewrite \
  -H 'Content-Type: application/json' \
  -d '{"text": "Your text here", "model": "llama3.2"}'

# Configuration
curl http://localhost:8000/api/config
```

---

## Chrome Extension

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `extension/` directory
4. The extension automatically strips invisible characters when copying
5. Right-click selected text → **AntiWatermark** → **Clean Selection** or **Rewrite Selection Locally**

---

## Project Structure

```
AntiWatermark/
├── antiwatermark/
│   ├── core.py          # Cleaning, shielding, validation, diagnostics
│   ├── backend.py       # RewriterBackend, BuiltinBackend, OllamaBackend
│   ├── middleware.py     # Rewrite orchestration, domain personas
│   ├── cli.py           # Command-line interface
│   └── __init__.py
├── web/
│   └── index.html       # Self-contained Web UI
├── extension/
│   ├── manifest.json
│   ├── background.js
│   ├── content.js
│   ├── popup.html
│   └── popup.js
├── tests/
│   ├── test_core.py
│   ├── test_backend.py
│   └── test_api.py
├── scripts/
│   └── clipboard_daemon.py
├── app.py               # Local HTTP server
├── pyproject.toml
└── README.md
```

---

## Testing

```bash
pytest
```

99 tests covering:

- Invisible Unicode removal
- Cleaning idempotency
- Code/LaTeX/URL/Markdown/email preservation
- Collision-safe placeholders
- Validation gates
- Builtin backend
- Local-only security policy
- API endpoints

---

## What AntiWatermark Does

| Feature | Description |
|---------|-------------|
| Strip invisible chars | Removes 26+ zero-width Unicode characters used for text fingerprinting |
| Replace AI clichés | Deterministically replaces 30+ common AI writing patterns |
| Protect structured content | Shields code blocks, LaTeX, URLs, links, and emails from modification |
| Validate output | 5-gate validation ensures protected content is preserved |
| Heuristic diagnostics | Analyzes text patterns, burstiness, and AI marker density |
| Local neural rewrite | Optional deeper rewriting via local Ollama models |

---

## What AntiWatermark Does NOT Do

- ❌ No cloud API calls
- ❌ No data exfiltration
- ❌ No API keys required
- ❌ No torch/transformers dependencies
- ❌ No automatic model downloads
- ❌ No detector score manipulation claims

---

## Security

All neural communication is restricted to loopback addresses only:

- `127.0.0.1` ✅
- `localhost` ✅
- `::1` ✅
- Any remote host ❌ **Rejected**

The `LocalOnlyPolicy` class enforces this at the backend level.

---

## License

MIT
