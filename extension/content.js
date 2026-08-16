/**
 * AntiWatermark Chrome Content Script
 * Injected on Claude.ai, Gemini, and ChatGPT
 */

(function () {
  const INVISIBLE_CODEPOINTS = [
    '\u200B', '\u200C', '\u200D', '\u200E', '\u200F',
    '\u202A', '\u202B', '\u202C', '\u202D', '\u202E',
    '\u2060', '\u2061', '\u2062', '\u2063', '\u2064',
    '\u206A', '\u206B', '\u206C', '\u206D', '\u206E', '\u206F',
    '\uFEFF', '\u00AD', '\u180E', '\u034F',
    '\u115F', '\u1160', '\u3164', '\uFFA0'
  ];
  const INVISIBLE_REGEX = new RegExp('[' + INVISIBLE_CODEPOINTS.join('') + ']', 'g');

  function stripInvisible(text) {
    return text.replace(INVISIBLE_REGEX, '').normalize('NFKC');
  }

  // Intercept Copy Events on AI web pages to auto-strip invisible watermarks
  document.addEventListener('copy', function (e) {
    const selection = window.getSelection().toString();
    if (selection) {
      const cleaned = stripInvisible(selection);
      if (cleaned !== selection) {
        e.clipboardData.setData('text/plain', cleaned);
        e.preventDefault();
        showNotification("🧹 AntiWatermark: Stripped invisible watermarks on copy!");
      }
    }
  });

  function showNotification(msg) {
    let toast = document.createElement('div');
    toast.innerText = msg;
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.background = '#1f2937';
    toast.style.color = '#3fb950';
    toast.style.padding = '10px 16px';
    toast.style.borderRadius = '8px';
    toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
    toast.style.zIndex = '999999';
    toast.style.fontFamily = 'sans-serif';
    toast.style.fontSize = '13px';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2500);
  }

  console.log("🛡️ AntiWatermark content script active on", window.location.hostname);
})();
