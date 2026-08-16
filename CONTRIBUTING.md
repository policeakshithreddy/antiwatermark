# Contributing to AntiWatermark

Thank you for your interest in improving **AntiWatermark**! We welcome contributions from developers, researchers, and writers.

---

## 🛠️ How to Contribute

### 1. Reporting Bugs
* Open an issue describing the bug.
* Include the input text, the expected output, and the actual scorecard result.
* Specify whether the issue occurred in the CLI, Web UI, or Chrome Extension.

### 2. Suggesting New Features or AI Markers
* Open a Feature Request issue.
* If you discover a new overused AI buzzword, trope, or language pattern (e.g. Italian, Japanese, Hindi), please provide examples and recommended human replacements.

### 3. Submitting Pull Requests (PRs)
1. Fork the repository and create a new branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Make your improvements.
3. Verify that the test suite and build run cleanly:
   ```bash
   pytest
   python3 -m build
   ```
4. Commit your changes with clear, conventional commit messages:
   ```bash
   git commit -m "feat: add Italian AI buzzword dictionary"
   ```
5. Push to your fork and submit a Pull Request.

---

## 📜 Development Guidelines
* **Code & Math Protection:** Ensure any changes to the regex cleaner never alter text inside code blocks (```` ``` ````) or LaTeX math (`$$...$$`).
* **Cross-Platform:** Scripts must work across macOS, Linux, and Windows.
* **License:** All contributions will be licensed under the MIT License.
