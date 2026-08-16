const INVISIBLE_CODEPOINTS = [
  '\u200B', '\u200C', '\u200D', '\u200E', '\u200F',
  '\u202A', '\u202B', '\u202C', '\u202D', '\u202E',
  '\u2060', '\u2061', '\u2062', '\u2063', '\u2064',
  '\u206A', '\u206B', '\u206C', '\u206D', '\u206E', '\u206F',
  '\uFEFF', '\u00AD', '\u180E', '\u034F',
  '\u115F', '\u1160', '\u3164', '\uFFA0'
];
const INVISIBLE_REGEX = new RegExp('[' + INVISIBLE_CODEPOINTS.join('') + ']', 'g');

const AI_BUZZWORDS = [
  /\bdelve(s|d|ing)?\b/gi, /\btapestry\b/gi, /\btestament\b/gi, /\bmultifaceted\b/gi,
  /\bholistic\b/gi, /\bbeacon\b/gi, /\bfoster(s|ed|ing)?\b/gi, /\bnuanced\b/gi,
  /\bunderscores?\b/gi, /\bpivotal\b/gi, /\bparamount\b/gi, /\bcrucial role\b/gi,
  /\bin conclusion\b/gi, /\bfurthermore\b/gi, /\bmoreover\b/gi, /\bintertwined\b/gi,
  /\bgame-changer\b/gi, /\brevolutioniz(e|es|ed|ing)\b/gi, /\bcertainly!?\b/gi
];

function sanitize(text) {
  let invisMatches = (text.match(INVISIBLE_REGEX) || []).length;
  let cleaned = text.replace(INVISIBLE_REGEX, '').normalize('NFKC');
  return { cleaned, invisMatches };
}

const inputEl = document.getElementById('textInput');
const statsEl = document.getElementById('stats');

document.getElementById('cleanBtn').addEventListener('click', () => {
  const { cleaned, invisMatches } = sanitize(inputEl.value);
  inputEl.value = cleaned;
  
  let markers = [];
  AI_BUZZWORDS.forEach(r => {
    let m = cleaned.match(r);
    if (m) markers.push(...m);
  });

  statsEl.innerText = `Stripped ${invisMatches} invisible chars | ${markers.length} AI markers detected`;
});

document.getElementById('copyBtn').addEventListener('click', () => {
  navigator.clipboard.writeText(inputEl.value);
  statsEl.innerText = "✅ Copied clean text to clipboard!";
});
