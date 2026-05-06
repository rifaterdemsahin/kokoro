# Error Log

## [2026-05-06] Gemini Enhancement Returns Markdown Asterisks — TTS Reads "Star"

**Symptom:**
After clicking "Enhance Text", the enhanced story about Elias the bridge builder still contained asterisks around emphasized words (e.g., `*imagination*`, `*sinthome*`, `**word**`). When passed to the TTS engine, these markdown markers are either read aloud as "star" or cause unnatural pauses, making the voiceover sound broken.

**Root cause:**
1. **LLM training bias:** Gemini (and most LLMs) are trained on vast corpora of markdown-formatted text. When asked to "enhance" or "make something sound better," the model's default behavior is to apply markdown emphasis (`*italics*`, `**bold**`) because that is how emphasis is commonly expressed in plain text interfaces.
2. **Insufficient prompt constraints:** The original enhancement prompt did not explicitly forbid markdown formatting. It only asked for "natural, conversational" text and to "respond ONLY with the enhanced text." Without a negative constraint (`Do NOT use...`), the model freely inserted asterisks.
3. **TTS engines are markdown-naive:** Kokoro and Edge-TTS treat the input string literally. They do not parse markdown. Therefore `*word*` becomes "star word star" or an awkward phonetic glitch rather than an emphasized "word."

**Fix applied:**
- **Prompt hardening (`main.py`):** The Gemini prompt now explicitly includes:  
  `"Do NOT use markdown formatting such as asterisks, bold, italics, or underscores. Use plain text only."`
- **Server-side regex guard (`main.py`):** Added `re.sub()` to strip any remaining `*...*`, `**...**`, `_..._`, `__...__` patterns, plus a final `.replace('*', '')` to catch strays.
- **Client-side fallback (`index.html`):** Added identical regex cleanup in JavaScript before writing the enhanced text into the textarea, ensuring the UI layer is protected even if the server logic is bypassed or outdated.

**Workaround active:** No — this is a permanent fix with defense in depth.

**Linked to:** [4_Formula/tts_text_preparation.md] (if created), [5_Symbols/main.py], [5_Symbols/index.html]

---

## Why This Happened — Deeper Analysis

### The "Sinthome" Problem

The user's input text itself contained italicized concepts wrapped in asterisks (`*imagination*`, `*words*`, `*hard reality*`). Gemini, being a helpful assistant, preserved and even amplified this stylistic choice during enhancement. The model interpreted the asterisks as intentional emphasis and replicated them throughout the output.

### The Invisible Character Trap

Markdown emphasis is invisible to human readers in rendered form but becomes **highly visible** to a TTS engine. This is a classic impedance mismatch between:
- **Visual systems** (browsers, markdown renderers) where `*word*` = *word*
- **Auditory systems** (TTS engines) where `*word*` = "star word star"

### Prevention Pattern

For any LLM → TTS pipeline, always include:
1. **Explicit negative constraints** in the prompt ("Do NOT use X")
2. **Output sanitization** before passing to the speech engine
3. **Visual inspection** or automated test for markdown characters in TTS inputs

---

## Near-Misses

- **Underscores (`_word_`)**: The same issue could occur with underscore-based markdown emphasis. The regex handles both `*` and `_` variants.
- **Other markdown (lists, headers)**: While not observed yet, Gemini could theoretically return bullet points (`- item`) or headers (`# Title`). The current fix only targets emphasis markers. If list formatting appears, a broader markdown stripper may be needed.
- **Turkish text**: Turkish enhancement uses the same prompt. If Turkish markdown conventions differ (they don't for basic emphasis), the same fix applies.

---

## Lessons Learned

1. **LLMs are not TTS-aware by default.** You must bridge the gap explicitly.
2. **Negative constraints in prompts are as important as positive instructions.** "Do NOT use markdown" is more effective than "respond with plain text."
3. **Defense in depth matters.** Prompt engineering + server-side cleanup + client-side cleanup = resilient system.
4. **Log these incidents.** If the model behavior changes in a future update, we have a record of what worked.

---

*Logged in 6_Semblance as per Project Self-Learning System — Stage 6: The Scars.*
