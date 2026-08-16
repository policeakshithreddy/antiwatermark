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

function stripInvisible(text) {
  return text.replace(INVISIBLE_REGEX, '').normalize('NFKC');
}

function humanize(text) {
  let result = text;
  for (const { pattern, replacement } of LEXICAL_REPLACEMENTS) {
    result = result.replace(pattern, replacement);
  }
  return result;
}

function showToast(message, type = 'success') {
  const existing = document.getElementById('antiwatermark-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'antiwatermark-toast';
  toast.style.cssText = `
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: hsl(220, 18%, 10%);
    color: hsl(220, 15%, 90%);
    padding: 12px 20px;
    border-radius: 8px;
    border: 1px solid hsl(220, 14%, 18%);
    border-left: 4px solid ${type === 'error' ? 'hsl(0, 70%, 55%)' : 'hsl(145, 60%, 45%)'};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 13px;
    font-weight: 500;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    z-index: 2147483647;
    display: flex;
    align-items: center;
    gap: 8px;
    animation: awSlideIn 0.25s ease-out;
  `;

  toast.innerHTML = `
    <span>${message}</span>
    <style>
      @keyframes awSlideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
    </style>
  `;

  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

document.addEventListener('copy', (e) => {
  chrome.storage.local.get(['autoCleanClipboard'], (result) => {
    if (result.autoCleanClipboard !== false) {
      const selection = document.getSelection()?.toString();
      if (selection) {
        const cleaned = stripInvisible(selection);
        if (cleaned !== selection) {
          e.clipboardData.setData('text/plain', cleaned);
          e.preventDefault();
          showToast(`🛡️ AntiWatermark: Stripped ${selection.length - cleaned.length} invisible characters`);
        }
      }
    }
  });
});

chrome.runtime.onMessage.addListener(async (request, sender, sendResponse) => {
  if (request.action === 'clean_selection') {
    const cleaned = humanize(stripInvisible(request.text));
    try {
      await navigator.clipboard.writeText(cleaned);
      showToast('🛡️ AntiWatermark: Selection cleaned and copied');
    } catch (err) {
      showToast('Failed to copy to clipboard', 'error');
    }
  } else if (request.action === 'rewrite_selection') {
    showToast('🔄 AntiWatermark: Rewriting locally...');
    try {
      chrome.storage.local.get(['modelName'], async (result) => {
        const model = result.modelName || 'llama3.2';
        const response = await fetch('http://localhost:8000/api/rewrite', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: request.text, model })
        });
        if (!response.ok) throw new Error('Rewrite failed');
        const data = await response.json();
        const textToCopy = data.text || data.rewritten_text || request.text;
        await navigator.clipboard.writeText(textToCopy);
        showToast('✅ AntiWatermark: Rewrite complete & copied!');
      });
    } catch (err) {
      showToast('Rewrite failed. Ensure AntiWatermark server is running.', 'error');
    }
  }
});
