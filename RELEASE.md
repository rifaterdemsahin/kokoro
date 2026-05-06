# Release Notes

> Project: Kokoro TTS  
> Template: Delivery Pilot v0.9  
> Updated: 2026-05-06

---

## Current Release: v0.9.0

### ✨ New Features

#### 1. Interactive How-to-Use Guide Popup (2026-05-06)
- **Commit:** `32a984e`
- Added a `?` help button in the top-right corner of the UI.
- Clicking opens a dark-themed modal with a 5-step guide:
  1. Quick Start
  2. Enhance Text (AI-Powered)
  3. Voice & Speed
  4. Download
  5. Tips
- Fully bilingual: switches between **English** and **Turkish** based on the language dropdown.
- Closes via `Escape` key, clicking outside, or the `×` button.

#### 2. AI Text Enhancement with Gemini (2026-04-26)
- **Commit:** `a6f3f02`
- Added **"Enhance Text"** button powered by `gemini-2.5-flash`.
- Polishes user input for voiceover: adds natural punctuation, fixes pacing, improves flow.
- Supports both English and Turkish enhancement prompts.

#### 3. Dynamic Filename Generation (2026-04-26)
- **Commit:** `15a31b4`, `3764d90`
- Downloads are no longer named generic `kokoro-audio.mp3`.
- Gemini generates a 2-3 word slug from the text content.
- Example: `bridge-builder-story.mp3`

#### 4. Multi-Language UI (EN/TR) (2026-04-25)
- **Commit:** `27ef7e6`, `b52cdf6`
- Full bilingual interface: all labels, placeholders, buttons, and messages switch dynamically.
- Language toggle in the top-right corner.
- Voice lists update automatically based on selected language.

#### 5. Edge-TTS Turkish Voices (2026-04-26)
- **Commit:** `a6f3f02`
- Added Turkish voices (`tr-TR-EmelNeural`, `tr-TR-AhmetNeural`) via Microsoft Edge-TTS.
- Turkish requests bypass Kokoro and use Edge-TTS for native accent support.
- Speed control works for both backends.

#### 6. Debug Panel (2026-05-06)
- **Commit:** `fc10a27`
- Added a visible **Debug Panel** at the bottom of the page.
- Documents active fixes (e.g., markdown asterisk cleanup) so users understand what the system is doing under the hood.

---

### 🛠 Fixes & Improvements

#### Markdown Asterisk Cleanup (2026-05-06)
- **Commit:** `fc10a27`, `365638e`
- **Problem:** Gemini enhancement returned markdown emphasis (`*word*`, `**word**`), which TTS engines read as "star word star."
- **Solution:** Defense-in-depth approach:
  1. **Prompt hardening:** Explicitly forbids markdown in the Gemini prompt.
  2. **Server-side regex:** Strips `*...*`, `**...**`, `_..._`, `__...__` and stray asterisks in `main.py`.
  3. **Client-side fallback:** Identical regex cleanup in JavaScript before writing to the textarea.
  4. **Documentation:** Added error log in `6_Semblance/error_log.md` explaining root cause and prevention pattern.

#### Docker & Deployment Fixes (2026-04-25)
- **Commit:** `759a785`
- Fixed `index.html` not being copied into the Docker container during build.

#### Doppler Secrets Management (2026-04-25)
- **Commit:** `8ad1385`, `eea4a88`, `2682630`
- Added guides and formulas for syncing Doppler secrets to Fly.io.
- Documented secrets management workflow in `4_Formula/`.
- Added simulation screenshot of Doppler dashboard to `3_Simulation/`.

---

### 📁 Project Structure

This project follows the **Project Self-Learning System — 7-Stage Journey**:

```
delivery-pilot-template/
├── 1_Real_Unknown/       # Problem definitions, OKRs, core questions
├── 2_Environment/        # Roadmaps, constraints, setup guides
├── 3_Simulation/         # UI mockups, dynamic image carousel
├── 4_Formula/            # Step-by-step guides, research notes, build logic
├── 5_Symbols/            # Source code (main.py, index.html, Dockerfile)
├── 6_Semblance/          # Error logs, near-misses, workarounds
├── 7_Testing_Known/      # Validation, testing checklists, outcomes
├── index.html            # Main frontend UI
├── main.py               # FastAPI backend
├── Dockerfile
├── fly.toml
├── requirements.txt
├── README.md
└── RELEASE.md            # ← This file
```

---

### 🔧 Technical Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML/CSS/JS (dark mode, responsive) |
| Backend | FastAPI (Python) |
| TTS Engine | Kokoro-82M ONNX Runtime |
| Turkish TTS | Microsoft Edge-TTS |
| AI Enhancement | Google Gemini 2.5 Flash |
| Hosting | Fly.io (auto-stop/start) |
| Secrets | Doppler |
| CI/CD | GitHub Actions (GitHub Pages) |

---

### 🧪 Testing Checklist

- [x] GitHub Pages building via GitHub Actions
- [x] All 7 folders exist with content
- [x] Navigation/structure works
- [x] Debug mode documented
- [x] All markdown files render
- [x] Secrets managed via Doppler (not in git)
- [x] `index.html` links to GitHub, LinkedIn, YouTube
- [x] README.md contains Fly.io URL
- [x] TTS generation works for English (Kokoro) and Turkish (Edge-TTS)
- [x] Gemini enhancement strips markdown correctly
- [x] Guide popup renders in both EN and TR
- [x] Dynamic filenames generated from text content

---

### 📝 Known Issues & Technical Debt

| Issue | Status | Location |
|-------|--------|----------|
| First request after cold start takes ~15s | Expected | Fly.io auto-stop/start |
| Markdown list/header cleanup not implemented | Low priority | `main.py` enhancement endpoint |
| No audio waveform visualization | Feature idea | Future release |

---

### 🚀 Deployment

```bash
# Local
uvicorn main:app --reload

# Fly.io
flyctl deploy
```

---

*Maintained under the Project Self-Learning System framework.*
