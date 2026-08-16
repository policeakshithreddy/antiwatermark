const INVISIBLE_CODEPOINTS = [
  '\u200B', '\u200C', '\u200D', '\u200E', '\u200F',
  '\u202A', '\u202B', '\u202C', '\u202D', '\u202E',
  '\u2060', '\u2061', '\u2062', '\u2063', '\u2064',
  '\u206A', '\u206B', '\u206C', '\u206D', '\u206E', '\u206F',
  '\uFEFF', '\u00AD', '\u180E', '\u034F',
  '\u115F', '\u1160', '\u3164', '\uFFA0'
];
const INVISIBLE_REGEX = new RegExp('[' + INVISIBLE_CODEPOINTS.join('') + ']', 'g');

const LEXICAL_REPLACEMENTS = [
  { pattern: /\bdelve(s|d|ing)? into\b/gi, replacement: "explore" },
  { pattern: /\bdelve(s|d|ing)?\b/gi, replacement: "examine" },
  { pattern: /\brich tapestry of\b/gi, replacement: "mix of" },
  { pattern: /\btapestry of\b/gi, replacement: "blend of" },
  { pattern: /\btapestry\b/gi, replacement: "landscape" },
  { pattern: /\bstands as a testament to\b/gi, replacement: "shows" },
  { pattern: /\ba testament to\b/gi, replacement: "evidence of" },
  { pattern: /\btestament\b/gi, replacement: "proof" },
  { pattern: /\bmultifaceted\b/gi, replacement: "complex" },
  { pattern: /\bholistic\b/gi, replacement: "comprehensive" },
  { pattern: /\bbeacon of\b/gi, replacement: "model for" },
  { pattern: /\bfoster(ing)?\b/gi, replacement: "encouraging" },
  { pattern: /\bnuanced\b/gi, replacement: "detailed" },
  { pattern: /\bunderscores?\b/gi, replacement: "highlights" },
  { pattern: /\bpivotal\b/gi, replacement: "key" },
  { pattern: /\bparamount\b/gi, replacement: "essential" },
  { pattern: /\bplays a (crucial|pivotal|critical) role in\b/gi, replacement: "is key to" },
  { pattern: /\bcrucial role\b/gi, replacement: "important role" },
  { pattern: /\bcrucial\b/gi, replacement: "important" },
  { pattern: /\bgame-changer\b/gi, replacement: "major step forward" },
  { pattern: /\brevolutioniz(e|es|ed|ing)\b/gi, replacement: "transforms" },
  { pattern: /\bseamlessly\b/gi, replacement: "smoothly" },
  { pattern: /\bintertwined\b/gi, replacement: "connected" },
  { pattern: /\bharness(ing)? the power of\b/gi, replacement: "using" },
  { pattern: /\bCertainly!?\s*/gi, replacement: "" },
  { pattern: /\bSure thing!?\s*/gi, replacement: "" }
];

function quickClean(text) {
  let cleaned = text.replace(INVISIBLE_REGEX, '').normalize('NFKC');
  for (const { pattern, replacement } of LEXICAL_REPLACEMENTS) {
    cleaned = cleaned.replace(pattern, replacement);
  }
  return cleaned;
}

document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('input-text');
  const processBtn = document.getElementById('process-btn');
  const resultContainer = document.getElementById('result-container');
  const resultArea = document.getElementById('result-area');
  const copyBtn = document.getElementById('copy-btn');
  const settingsToggle = document.getElementById('settings-toggle');
  const settingsPanel = document.getElementById('settings-panel');
  
  const modelNameInput = document.getElementById('model-name');
  const autoCleanInput = document.getElementById('auto-clean');

  // Load settings
  chrome.storage.local.get(['modelName', 'autoCleanClipboard'], (res) => {
    if (res.modelName) modelNameInput.value = res.modelName;
    if (res.autoCleanClipboard !== undefined) autoCleanInput.checked = res.autoCleanClipboard;
  });

  // Save settings
  modelNameInput.addEventListener('change', () => {
    chrome.storage.local.set({ modelName: modelNameInput.value });
  });
  autoCleanInput.addEventListener('change', () => {
    chrome.storage.local.set({ autoCleanClipboard: autoCleanInput.checked });
  });

  // Settings toggle
  settingsToggle.addEventListener('click', () => {
    settingsPanel.classList.toggle('active');
  });

  // Process
  processBtn.addEventListener('click', async () => {
    const text = input.value.trim();
    if (!text) return;

    const mode = document.querySelector('input[name="mode"]:checked').value;
    
    resultContainer.style.display = 'block';
    
    if (mode === 'clean') {
      resultArea.value = quickClean(text);
    } else {
      processBtn.disabled = true;
      processBtn.textContent = 'Rewriting...';
      try {
        const model = modelNameInput.value || 'llama3.2';
        const response = await fetch('http://localhost:8000/api/rewrite', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, model })
        });
        if (!response.ok) throw new Error('Request failed with status ' + response.status);
        const data = await response.json();
        resultArea.value = data.text || data.rewritten_text;
      } catch (err) {
        resultArea.value = 'Error: ' + err.message + '\nEnsure the local AntiWatermark server is running on port 8000.';
      } finally {
        processBtn.disabled = false;
        processBtn.textContent = 'Process';
      }
    }
  });

  // Copy
  copyBtn.addEventListener('click', async () => {
    if (resultArea.value) {
      await navigator.clipboard.writeText(resultArea.value);
      const originalText = copyBtn.textContent;
      copyBtn.textContent = 'Copied!';
      setTimeout(() => copyBtn.textContent = originalText, 2000);
    }
  });
});
