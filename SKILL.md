---
name: ai-watermark-remover
description: >-
  Systematically strips AI watermarks, Google SynthID-Text, statistical token fingerprints (Kirchenbauer/Gumbel),
  zero-width steganographic characters, and characteristic Claude/Gemini/GPT stylistic markers from text.
  Use when asked to "dewatermark text", "remove Claude/Gemini watermarks", "break SynthID", "humanize AI text",
  "make text pass AI detectors", or "rewrite without AI tropes".
---

# AI Text Watermark Remover Skill (Claude, Gemini, SynthID & GPT)

This skill provides an end-to-end operational protocol to detect and eliminate all forms of AI text watermarking across **Claude (Anthropic)**, **Gemini & SynthID-Text (Google DeepMind)**, and **GPT (OpenAI)**.

It targets three distinct watermarking layers:
1. **Invisible Steganography** (Zero-width characters, homoglyphs, invisible separators).
2. **Statistical / $n$-gram Logit Watermarks** (**Google SynthID-Text**, Kirchenbauer green/red list, Aaronson Gumbel watermarks).
3. **Model-Specific Stylistic Fingerprints** (Claude-isms, Gemini tropes, predictable cadence, and low-entropy formatting).

---

## 1. The Anatomy of AI Text Watermarks

Modern AI text generators (including Claude, GPT, and Gemini) leave traces across three distinct vectors:

| Watermark Type | Mechanism | Detection Method | Removal Strategy |
| :--- | :--- | :--- | :--- |
| **Steganographic / Unicode** | Invisible zero-width spaces (`\u200B`), non-joiners (`\u200C`), directional marks, or homoglyphs injected during copying/generation. | Byte-level scanning, Unicode inspect. | Deterministic stripping regex and NFKC normalization. |
| **Statistical / $n$-gram Logits** | Pseudo-random token selection biasing $n$-gram transitions into a "green list" (SynthID, Kirchenbauer). | $z$-score hypothesis testing across token sequences. | Syntactic permutation, synonym swapping, clause shifting, breaking $n$-gram hash chains. |
| **Stylistic / Entropy Markers** | Overused vocabulary, uniform sentence lengths (low burstiness), low perplexity, symmetrical list structures, excessive hedging. | Classifiers (Turnitin, GPTZero, CopyLeaks). | Lexical substitution, varying sentence lengths (4 to 28 words), removing AI clichés, eliminating symmetrical lists. |

---

## 2. The 5-Stage Dewatermarking Protocol

When given text to dewatermark, execute the following 5 stages sequentially:

```
[Input Text]
     │
     ▼
┌────────────────────────────────────────────────────────┐
│ Stage 1: Deterministic Unicode & Binary Sanitization   │ ➔ Strip zero-width chars & normalize NFKC
└────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│ Stage 2: Statistical $n$-gram Chain Shattering          │ ➔ Reorder clauses & switch voice (breaks SynthID)
└────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│ Stage 3: Lexical & Stylistic "De-Claude-ification"     │ ➔ Replace 50+ AI clichés & strip hedging
└────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│ Stage 4: Burstiness & Perplexity Calibration           │ ➔ Inject rhythm variation & natural idioms
└────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│ Stage 5: Semantic & Fact-Checking Preservation         │ ➔ Verify 0% hallucination & 100% intent retained
└────────────────────────────────────────────────────────┘
     │
     ▼
[100% Clean, Humanized Text]
```

---

### Stage 1: Deterministic Unicode & Binary Sanitization

First, strip all invisible characters and normalize Unicode. 

**Regex to strip:**
`[\u200B\u200C\u200D\u200E\u200F\u202A-\u202E\u2060-\u206F\uFEFF\u00AD\u180E\u034F\u115F\u1160\u3164\uFFA0]`

*(You can run `python3 scripts/sanitize.py "<text>"` or execute the regex directly.)*

---

### Stage 2: Statistical $n$-gram Chain Shattering

Statistical watermarks (like SynthID) hash previous words $w_{t-k} \dots w_{t-1}$ to determine the pseudo-random score of token $w_t$. Disrupt this sequence:

1. **Clause Inversion**: Shift dependent clauses from the end of the sentence to the beginning, or vice versa.
   * *AI:* "Machine learning improves precision because it optimizes loss gradients."
   * *Clean:* "By optimizing loss gradients, machine learning delivers sharper precision."
2. **Voice Shifting**: Convert passive constructions into active voice with explicit agency, or split long compound sentences into crisp independent clauses.
3. **Punctuation & Connector Alteration**: Replace predictable transitions (*"Furthermore"*, *"Moreover"*) with contextual connectors (*"On top of that"*, *"In practice"*, *"Similarly"*, or simple conjunctions like *"And"* / *"But"*).

---

### Stage 3: Lexical & Stylistic "De-Claude & De-Gemini-ification"

Both Claude (Anthropic) and Gemini (Google) have recognizable vocabulary biases and structural mannerisms. Replace them systematically:

#### Banned AI Buzzwords & Substitutions:
- ❌ **delve / delve into / dive deep** ➔ investigate, explore, look at, examine, break down
- ❌ **rich tapestry / tapestry / treasure trove** ➔ mix, collection, blend, ecosystem, landscape
- ❌ **testament to / stands as a** ➔ proof of, evidence that, shows, reflects
- ❌ **multifaceted / nuanced / plethora / myriad** ➔ complex, layered, detailed, varied, wide range
- ❌ **beacon / beacon of / powerhouse** ➔ leader in, example of, model for, strong platform
- ❌ **foster / fostering / supercharge** ➔ encourage, build, support, grow, speed up, drive
- ❌ **underscores / highlights / shines a light** ➔ shows, stresses, makes clear, points to
- ❌ **pivotal / paramount / crucial / critical role** ➔ key, vital, essential, important, direct factor
- ❌ **game-changer / revolutionizes / transforms** ➔ major upgrade, big step forward, improves
- ❌ **harness the power of / unleash** ➔ use, apply, run, deploy, leverage
- ❌ **elevate / supercharge your workflow** ➔ improve, speed up, streamline, refine
- ❌ **intertwined / seamlessly** ➔ connected, combined, directly, smoothly
- ❌ **certainly! / sure thing! / here is a breakdown** ➔ *(Delete completely; start directly with the answer)*
- ❌ **let's unpack this / let's dive in** ➔ *(Delete completely; begin immediately)*
- ❌ **in conclusion / to sum up** ➔ *(Delete or use contextual closure: "Ultimately", "At its core")*
- ❌ **it is important to remember / keep in mind that** ➔ *(Delete; state the point directly)*

#### Banned Structural Tropes:
1. **The "Symmetrical Triad"**: AI frequently creates lists of exactly 3 bullet points with bold headers of identical length. **Fix:** Use varying list lengths (2, 4, or 5 items) or narrative paragraphs.
2. **The "Balanced Both-Sides Hedge"**: *"While X has merits, it is equally important to acknowledge Y."* **Fix:** Take a clear, decisive stance or state the tradeoff straightforwardly.
3. **The Em-Dash Overuse**: AI overuses `—` to append decorative thoughts. **Fix:** Use parentheses, commas, or start a new sentence.
4. **The "Bold Colon" Formatting**: Gemini & Claude heavily output `**Feature:** Explanation`. **Fix:** Integrate descriptions directly into natural running sentences.

---

### Stage 4: Burstiness & Perplexity Calibration

Human writing is asymmetrical and irregular. AI writing is overly uniform and predictable.

* **Sentence Length Burstiness**:
  * Write a 4-word sentence.
  * Follow it with an 18-word explanation providing technical context.
  * Follow that with a medium 10-word summary.
  * Target a sentence length standard deviation $\sigma > 8.0$.
* **Vocabulary Perplexity**:
  * Use specific, domain-exact nouns rather than broad conceptual abstractions.
  * Use colloquial phrasing where appropriate for tone (e.g., *"cut down"* instead of *"drastically mitigate"*).

---

### Stage 5: Semantic & Fact-Checking Preservation

* Ensure no technical terms, metrics, numerical values, or citations are lost or altered.
* Verify that tone matches the user's intent (Academic, Technical, Business, or Casual).

---

---

## 3. Multi-Domain Persona Presets

Select the target persona to match the required domain:

### 🎓 1. Academic & Scholarly Preset
* **Goal:** Pass Turnitin / GPTZero while retaining scientific rigor and exact citations.
* **Rules:**
  - Use precise, peer-reviewed domain terminology; avoid colloquialisms.
  - Eliminate rhetorical questions and filler (*"It is important to note"*, *"In conclusion"*).
  - Use active academic voice (*"The data indicates"* rather than *"It can be observed from the data that"*).
  - Maintain variable paragraph densities and asymmetrical citation groupings.

### 💻 2. Software Engineering & Technical Preset
* **Goal:** Direct, pragmatic technical documentation with 100% code syntax immunity.
* **Rules:**
  - **IMMUNITY SHIELD:** Never alter code inside ```` ``` ```` blocks, inline backticks ``` `code` ```, or terminal commands.
  - Strip promotional adjectives (*"revolutionary architecture"*, *"seamless scalability"*).
  - Explain mechanisms step-by-step with concrete inputs, outputs, and failure modes.

### 💼 3. Executive & Business Preset
* **Goal:** Crisp, action-oriented, data-first corporate communication.
* **Rules:**
  - Lead with bottom-line outcomes, metrics, percentages, and deadlines.
  - Drop conceptual fluff (*"delve into the landscape"*, *"harness the power"*).
  - Use asymmetrical bullet points (e.g., 2 or 4 items, varying in length and structure).

### ✍️ 4. Conversational & Creative Preset
* **Goal:** Authentic human storytelling with genuine voice and cadence.
* **Rules:**
  - Use natural contractions (*"didn't"*, *"won't"*, *"we've"*), idioms, and rhetorical pauses.
  - Break rhythmic predictability by placing 3-word punchy sentences after detailed observations.
  - Avoid formulaic summaries at the end.

---

## 4. Multi-Lingual Anti-Watermark Rules

AI watermarks appear across international languages. Apply these translation-specific bans:

* 🇪🇸 **Spanish:** Ban *"es fundamental destacar"*, *"un tapiz de"*, *"en conclusión"*, *"un papel crucial"*, *"desempeña un papel"*, *"un faro de"*.
* 🇫🇷 **French:** Ban *"il convient de noter"*, *"un rôle primordial"*, *"témoignage de"*, *"en conclusion"*, *"un éventail de"*, *"un phare de"*.
* 🇩🇪 **German:** Ban *"es ist wichtig zu beachten"*, *"ein facettenreicher"*, *"zusammenfassend lässt sich sagen"*, *"eine entscheidende rolle"*, *"ein meilenstein"*.

---

## 5. Universal Dewatermarking Prompts

### General Dewatermarking Prompt
```text
Rewrite the following text using the ai-watermark-remover protocol.
Domain Persona: [Academic / Technical / Business / Casual]

Strict Rules:
1. Strip all AI buzzwords (delve, tapestry, testament, multifaceted, foster, beacon, nuanced, underscores, paramount, crucial role, harness the power, supercharge, let's unpack).
2. Shatter n-gram sequences (SynthID) by inverting clauses and switching between active and passive forms.
3. Inject burstiness: mix punchy 4-word sentences with longer 20+ word compound sentences.
4. Protect all code blocks, syntax, and math equations ($...$) completely intact.
5. Make the tone authentic, authoritative, and direct.

Text to dewatermark:
"""
[PASTE TEXT HERE]
"""
```

---

## 6. Testing & Automated Scorecard

Run the offline detector simulator on any text or file:

```bash
# Run heuristic scorecard (Human %, Burstiness, SynthID risk, Markers)
python3 scripts/sanitize.py "<text or file_path>"

# Output JSON for pipeline integration
python3 scripts/sanitize.py input.md --json

# Run real-time clipboard monitor
python3 scripts/clipboard_daemon.py
```
- Detection Checkers (GPTZero / Turnitin / CopyLeaks): `< 10% AI Probability`
