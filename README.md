```button
name 🗄️ Move to Archive
type command
action Shell commands: Execute: Archive Current File
```

# Kokoro TTS — Paste Text, Get Audio

A dark-mode, bilingual (EN/TR) Text-to-Speech web app powered by **Kokoro-82M**, **Google Gemini**, and **Microsoft Edge-TTS**. Running on [Fly.io](https://fly.io) with zero cloud-credit cost.

**Live URL:** [https://secondbrain-kokoro.fly.dev/](https://secondbrain-kokoro.fly.dev/)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎙️ **Instant TTS** | Paste text, pick a voice, get audio in seconds. No signup. No credits. |
| 🤖 **AI Text Enhancement** | Click "Enhance Text" to let Gemini polish your writing for voiceover. Adds punctuation, fixes pacing, removes markdown. |
| 🌐 **Bilingual UI** | Full English / Turkish interface with dynamic language switching. |
| 🔊 **Dual TTS Backends** | English voices use **Kokoro-82M** (ONNX). Turkish voices use **Edge-TTS** for native accent. |
| 🏷️ **Smart Filenames** | Downloads are auto-named from your text content (e.g., `bridge-builder-story.mp3`). |
| ⚡ **Speed Control** | Adjust speech rate from 0.5x (slow) to 1.5x (fast). |
| 📖 **Built-in Guide** | Click the `?` button for a step-by-step how-to popup. |
| 🛠 **Debug Panel** | Transparent documentation of active fixes and system behavior. |
| 🔒 **Secrets via Doppler** | API keys managed externally — never committed to git. |

---

## 🚀 Quick Start

### Web UI
1. Go to [https://secondbrain-kokoro.fly.dev/](https://secondbrain-kokoro.fly.dev/)
2. Paste your text (max 5,000 chars).
3. (Optional) Click **Enhance Text** to polish with Gemini.
4. Pick a voice and speed.
5. Click **Generate Audio**.
6. Play, pause, or download the MP3.

### API Endpoint
```bash
curl -X POST https://secondbrain-kokoro.fly.dev/tts \
  -F "text=Hello world" \
  -F "voice=af_heart" \
  -F "speed=1.0" \
  --output hello.mp3
```

### Enhance Endpoint
```bash
curl -X POST https://secondbrain-kokoro.fly.dev/enhance \
  -F "text=Hello world" \
  -F "lang=en"
```

---

## 🏗 Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────────┐
│   User      │──────▶│  index.html │──────▶│   main.py       │
│  (Browser)  │◀──────│  (Frontend) │◀──────│  (FastAPI)      │
└─────────────┘      └─────────────┘      └─────────────────┘
                                                   │
                    ┌──────────────┬───────────────┴──────────┐
                    ▼              ▼                          ▼
              ┌─────────┐   ┌──────────┐              ┌────────────┐
              │ Kokoro  │   │ Edge-TTS │              │   Gemini   │
              │  ONNX   │   │ (Turkish)│              │  (Enhance) │
              └─────────┘   └──────────┘              └────────────┘
```

- **App Name:** `secondbrain-kokoro`
- **Region:** London (`lhr`)
- **Specs:** 2 shared vCPUs, 2 GB RAM
- **Cost:** ~$2/month (primarily shared IPv4 address)

---

## 🛠 Local Development

```bash
# 1. Clone
git clone https://github.com/rifaterdemsahin/kokoro.git
cd kokoro

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set secrets (use Doppler or .env)
export GEMINI_API_KEY="your-key"

# 4. Run
uvicorn main:app --reload --port 8080

# 5. Open http://localhost:8080
```

### Docker
```bash
docker build -t kokoro-tts .
docker run -p 8080:8080 -e GEMINI_API_KEY=$GEMINI_API_KEY kokoro-tts
```

---

## 🗣 Voices

### English (Kokoro-82M)
| ID | Name |
|----|------|
| `af_heart` | American Female — Heart |
| `af_bella` | American Female — Bella |
| `af_nicole`| American Female — Nicole |
| `am_adam`  | American Male — Adam |
| `am_michael`| American Male — Michael |
| `bf_emma`  | British Female — Emma |
| `bm_george`| British Male — George |

### Turkish (Edge-TTS)
| ID | Name |
|----|------|
| `tr-TR-EmelNeural` | Turkish Female — Emel |
| `tr-TR-AhmetNeural`| Turkish Male — Ahmet |

---

## 📂 Project Structure

This repo follows the **Project Self-Learning System — 7-Stage Journey**:

```
kokoro/
├── 1_Real_Unknown/       # Problem definitions, OKRs
├── 2_Environment/        # Roadmaps, constraints, setup guides
├── 3_Simulation/         # UI mockups, screenshots
├── 4_Formula/            # Step-by-step guides, research
├── 5_Symbols/            # Source code (main.py, index.html)
├── 6_Semblance/          # Error logs, workarounds, lessons learned
├── 7_Testing_Known/      # Validation, checklists
├── index.html            # Frontend UI
├── main.py               # FastAPI backend
├── Dockerfile
├── fly.toml              # Fly.io config
├── requirements.txt
├── README.md             # ← This file
└── RELEASE.md            # Changelog & release notes
```

---

## 🔐 Secrets Management

All secrets are managed via **Doppler**. Never commit API keys to git.

```bash
# Sync Doppler secrets to Fly.io
doppler secrets download --no-file --format docker > .env
flyctl secrets import < .env
```

See `4_Formula/doppler_secrets.md` for detailed instructions.

---

## 🐛 Recent Fixes

| Date | Issue | Fix |
|------|-------|-----|
| 2026-05-06 | Gemini returned markdown asterisks (`*word*`) | Prompt hardening + server-side regex + client-side fallback |
| 2026-05-06 | Users didn't know how to use the app | Added bilingual `?` guide popup |
| 2026-04-26 | Download filenames were generic | Added Gemini-powered slug generator |
| 2026-04-26 | No Turkish voice support | Integrated Edge-TTS for TR voices |
| 2026-04-25 | `index.html` missing from container | Fixed Dockerfile COPY step |

Full details in [`RELEASE.md`](RELEASE.md) and [`6_Semblance/error_log.md`](6_Semblance/error_log.md).

---

## 🧪 Testing Checklist

- [x] TTS generation works (English & Turkish)
- [x] Gemini enhancement strips markdown
- [x] UI switches languages (EN/TR)
- [x] Guide popup renders correctly
- [x] Dynamic filenames generated
- [x] Speed control affects playback
- [x] Secrets managed via Doppler
- [x] GitHub Actions CI/CD active
- [x] All 7 project folders populated

---

## 📜 License

See [LICENSE](LICENSE).

---

*Built with the Project Self-Learning System framework.*
