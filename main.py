#!/usr/bin/env python3
"""
Kokoro TTS Server — Fixed version with runtime model download.

Fix: Models download at server startup (not build time) because
HuggingFace requires auth tokens for some repos. GitHub releases
are used instead.
"""

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
import io
import os
import urllib.request
import soundfile as sf

app = FastAPI(title="Kokoro TTS Server")

# ── Model Download ──────────────────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "kokoro-v1.0.onnx")
VOICES_PATH = os.path.join(MODEL_DIR, "voices-v1.0.bin")

def download_file(url: str, dest: str):
    """Download a file if it doesn't exist."""
    if os.path.exists(dest):
        return
    print(f"[Kokoro] Downloading {os.path.basename(dest)}...")
    urllib.request.urlretrieve(url, dest)
    print(f"[Kokoro] Saved to {dest}")

def ensure_models():
    """Download ONNX model and voices if missing."""
    download_file(MODEL_URL, MODEL_PATH)
    download_file(VOICES_URL, VOICES_PATH)

# ── TTS Backend ─────────────────────────────────────────────────────
KOKORO_BACKEND = None
pipeline = None

def init_pipeline():
    """Lazy-init the TTS pipeline (downloads models on first call)."""
    global pipeline, KOKORO_BACKEND
    if pipeline is not None:
        return pipeline

    # Try kokoro-onnx first
    try:
        from kokoro_onnx import Kokoro
        ensure_models()
        pipeline = Kokoro(MODEL_PATH, VOICES_PATH)
        KOKORO_BACKEND = "onnx"
        print(f"[Kokoro] Loaded ONNX backend with {len(pipeline.voices)} voices")
        return pipeline
    except Exception as e:
        print(f"[Kokoro] ONNX failed: {e}")

    # Fallback to torch kokoro
    try:
        from kokoro import KPipeline
        pipeline = KPipeline(lang_code='a')
        KOKORO_BACKEND = "torch"
        print("[Kokoro] Loaded torch backend")
        return pipeline
    except Exception as e:
        print(f"[Kokoro] Torch failed: {e}")

    KOKORO_BACKEND = None
    return None

# ── Voices ──────────────────────────────────────────────────────────
VOICES = {
    "af_heart":  {"name": "American Female - Heart",  "gender": "female", "lang": "en-US"},
    "af_bella":  {"name": "American Female - Bella",  "gender": "female", "lang": "en-US"},
    "af_nicole": {"name": "American Female - Nicole", "gender": "female", "lang": "en-US"},
    "am_adam":   {"name": "American Male - Adam",     "gender": "male",   "lang": "en-US"},
    "am_michael":{"name": "American Male - Michael",  "gender": "male",   "lang": "en-US"},
    "bf_emma":   {"name": "British Female - Emma",    "gender": "female", "lang": "en-GB"},
    "bm_george": {"name": "British Male - George",    "gender": "male",   "lang": "en-GB"},
}

# ── HTML UI (embedded) ──────────────────────────────────────────────
HTML_UI = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kokoro TTS — Paste Text, Get Audio</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #0f0f23; color: #e0e0e0; padding: 20px;
            display: flex; flex-direction: column; align-items: center;
        }
        .container { width: 100%; max-width: 720px; }
        h1 {
            font-size: 2rem; margin-bottom: 8px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .header-top {
            display: flex; justify-content: space-between; align-items: center;
        }
        .lang-toggle {
            background: #1a1a2e; border: 1px solid #2a2a4a; color: #e0e0e0;
            padding: 5px 10px; border-radius: 6px; cursor: pointer;
            font-size: 0.9rem;
        }
        .lang-toggle:focus { outline: none; border-color: #667eea; }
        .subtitle { color: #888; margin-bottom: 30px; font-size: 0.95rem; }
        .card {
            background: #1a1a2e; border-radius: 16px; padding: 28px;
            margin-bottom: 20px; border: 1px solid #2a2a4a;
        }
        label {
            display: block; margin-bottom: 8px; font-size: 0.85rem;
            text-transform: uppercase; letter-spacing: 0.5px; color: #a0a0c0;
        }
        textarea {
            width: 100%; min-height: 180px; background: #0f0f23;
            border: 1px solid #2a2a4a; border-radius: 10px; padding: 14px;
            color: #e0e0e0; font-size: 1rem; line-height: 1.5;
            resize: vertical; transition: border-color 0.2s;
        }
        textarea:focus { outline: none; border-color: #667eea; }
        .controls {
            display: grid; grid-template-columns: 1fr 1fr;
            gap: 16px; margin-top: 16px;
        }
        select, input[type="range"] {
            width: 100%; background: #0f0f23; border: 1px solid #2a2a4a;
            border-radius: 10px; padding: 12px 14px; color: #e0e0e0;
            font-size: 0.95rem; cursor: pointer;
        }
        select:focus { outline: none; border-color: #667eea; }
        .speed-label {
            display: flex; justify-content: space-between;
            font-size: 0.85rem; color: #888; margin-top: 4px;
        }
        button.generate-btn {
            width: 100%; margin-top: 20px; padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none; border-radius: 10px; color: white;
            font-size: 1rem; font-weight: 600; cursor: pointer;
            transition: transform 0.15s, box-shadow 0.15s;
        }
        button.generate-btn:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
        }
        button.generate-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .status {
            margin-top: 16px; padding: 12px 16px; border-radius: 10px;
            font-size: 0.9rem; display: none;
        }
        .status.loading  { display: block; background: #1a2a4a; color: #7ab8ff; }
        .status.success  { display: block; background: #1a3a2a; color: #6ee7b7; }
        .status.error    { display: block; background: #3a1a1a; color: #ff7a7a; }
        audio { width: 100%; margin-top: 16px; border-radius: 10px; }
        .download-row { display: flex; gap: 10px; margin-top: 12px; }
        .download-row a {
            flex: 1; text-align: center; padding: 10px;
            background: #2a2a4a; border-radius: 8px; color: #e0e0e0;
            text-decoration: none; font-size: 0.9rem;
            transition: background 0.2s;
        }
        .download-row a:hover { background: #3a3a6a; }
        .footer { text-align: center; color: #555; font-size: 0.8rem; margin-top: 30px; }
        .char-count { text-align: right; font-size: 0.8rem; color: #666; margin-top: 4px; }
        @media (max-width: 480px) { .controls { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-top">
            <h1>Kokoro TTS</h1>
            <select id="uiLang" class="lang-toggle" onchange="switchLang()">
                <option value="en">English</option>
                <option value="tr">Türkçe</option>
            </select>
        </div>
        <p class="subtitle" id="t-subtitle">Paste text, pick a voice, get instant audio. No cloud. No credits.</p>
        <div class="card">
            <label for="text" id="t-your-text">Your Text</label>
            <textarea id="text" placeholder="Type or paste your text here...">Hello! This is Kokoro speaking from the cloud.</textarea>
            <div class="char-count" id="charCount">0 chars</div>
            <div class="controls">
                <div>
                    <label for="voice" id="t-voice">Voice</label>
                    <select id="voice">
                        <option value="af_heart" selected>AF Heart — Female (US)</option>
                        <option value="af_bella">AF Bella — Female (US)</option>
                        <option value="af_nicole">AF Nicole — Female (US)</option>
                        <option value="am_adam">AM Adam — Male (US)</option>
                        <option value="am_michael">AM Michael — Male (US)</option>
                        <option value="bf_emma">BF Emma — Female (UK)</option>
                        <option value="bm_george">BM George — Male (UK)</option>
                    </select>
                </div>
                <div>
                    <label for="speed" id="t-speed">Speed</label>
                    <input type="range" id="speed" min="0.5" max="1.5" step="0.1" value="1.0">
                    <div class="speed-label"><span id="t-slow">Slow</span><span id="speedVal">1.0x</span><span id="t-fast">Fast</span></div>
                </div>
            </div>
            <button class="generate-btn" id="generateBtn" onclick="generateAudio()">Generate Audio</button>
            <div class="status" id="status"></div>
            <audio id="player" controls style="display:none;"></audio>
            <div class="download-row" id="downloadRow" style="display:none;">
                <a id="downloadMp3" href="#" download="kokoro-audio.mp3">Download MP3</a>
            </div>
        </div>
        <p class="footer" id="t-footer">Powered by Kokoro-82M &middot; Running on fly.io</p>
    </div>
    <script>
        const i18n = {
            en: {
                subtitle: "Paste text, pick a voice, get instant audio. No cloud. No credits.",
                yourText: "Your Text",
                placeholder: "Type or paste your text here...",
                voice: "Voice",
                speed: "Speed",
                slow: "Slow",
                fast: "Fast",
                generateBtn: "Generate Audio",
                downloadMp3: "Download MP3",
                footer: "Powered by Kokoro-82M &middot; Running on fly.io",
                chars: "chars",
                errEmpty: "Please enter some text.",
                errTooLong: "Text too long. Max 5000 chars.",
                generating: "Generating audio... please wait (first load may take 15s).",
                success: "Audio ready! Playing now.",
                error: "Error: "
            },
            tr: {
                subtitle: "Metni yapıştırın, sesi seçin, anında ses alın. Bulut yok. Kredi yok.",
                yourText: "Metniniz",
                placeholder: "Metninizi buraya yazın veya yapıştırın...",
                voice: "Ses",
                speed: "Hız",
                slow: "Yavaş",
                fast: "Hızlı",
                generateBtn: "Ses Oluştur",
                downloadMp3: "MP3 İndir",
                footer: "Kokoro-82M tarafından desteklenmektedir &middot; fly.io üzerinde çalışıyor",
                chars: "karakter",
                errEmpty: "Lütfen bir metin girin.",
                errTooLong: "Metin çok uzun. Maksimum 5000 karakter.",
                generating: "Ses oluşturuluyor... lütfen bekleyin (ilk yükleme 15sn sürebilir).",
                success: "Ses hazır! Şimdi çalınıyor.",
                error: "Hata: "
            }
        };

        let currentLang = 'en';

        function switchLang() {
            currentLang = document.getElementById('uiLang').value;
            const t = i18n[currentLang];
            document.getElementById('t-subtitle').innerHTML = t.subtitle;
            document.getElementById('t-your-text').innerText = t.yourText;
            document.getElementById('text').placeholder = t.placeholder;
            document.getElementById('t-voice').innerText = t.voice;
            document.getElementById('t-speed').innerText = t.speed;
            document.getElementById('t-slow').innerText = t.slow;
            document.getElementById('t-fast').innerText = t.fast;
            document.getElementById('generateBtn').innerText = t.generateBtn;
            document.getElementById('downloadMp3').innerText = t.downloadMp3;
            document.getElementById('t-footer').innerHTML = t.footer;
            updateCharCount();
        }

        const textEl = document.getElementById('text');
        const voiceEl = document.getElementById('voice');
        const speedEl = document.getElementById('speed');
        const speedValEl = document.getElementById('speedVal');
        const btn = document.getElementById('generateBtn');
        const statusEl = document.getElementById('status');
        const player = document.getElementById('player');
        const downloadRow = document.getElementById('downloadRow');
        const downloadMp3 = document.getElementById('downloadMp3');
        const charCount = document.getElementById('charCount');

        function updateCharCount() {
            charCount.textContent = textEl.value.length + ' ' + i18n[currentLang].chars;
        }

        textEl.addEventListener('input', updateCharCount);
        updateCharCount();

        speedEl.addEventListener('input', () => {
            speedValEl.textContent = speedEl.value + 'x';
        });

        async function generateAudio() {
            const text = textEl.value.trim();
            const t = i18n[currentLang];
            if (!text) { showStatus(t.errEmpty, 'error'); return; }
            if (text.length > 5000) { showStatus(t.errTooLong, 'error'); return; }
            btn.disabled = true;
            showStatus(t.generating, 'loading');
            player.style.display = 'none'; downloadRow.style.display = 'none';
            try {
                const formData = new FormData();
                formData.append('text', text);
                formData.append('voice', voiceEl.value);
                formData.append('speed', speedEl.value);
                const response = await fetch('/tts', { method: 'POST', body: formData });
                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || 'Generation failed');
                }
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                player.src = url; player.style.display = 'block'; player.play();
                downloadMp3.href = url; downloadRow.style.display = 'flex';
                showStatus(t.success, 'success');
            } catch (err) {
                showStatus(t.error + err.message, 'error');
            } finally { btn.disabled = false; }
        }
        function showStatus(msg, type) {
            statusEl.textContent = msg;
            statusEl.className = 'status ' + type;
        }
    </script>
</body>
</html>
'''

# ── Endpoints ───────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_UI

@app.get("/voices")
def list_voices():
    return {"voices": VOICES}

@app.post("/tts")
def tts(
    text: str = Form(..., max_length=5000),
    voice: str = Form("af_heart"),
    speed: float = Form(1.0),
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    if voice not in VOICES:
        raise HTTPException(status_code=400, detail=f"Unknown voice: {voice}")

    pipe = init_pipeline()
    if pipe is None:
        raise HTTPException(
            status_code=503,
            detail="TTS engine failed to load. Check server logs."
        )

    try:
        if KOKORO_BACKEND == "onnx":
            samples, sample_rate = pipe.create(text, voice=voice, speed=speed)
        elif KOKORO_BACKEND == "torch":
            generator = pipe(text, voice=voice, speed=speed)
            for _, _, audio in generator:
                samples = audio
                sample_rate = 24000
                break
        else:
            raise HTTPException(status_code=503, detail="No TTS backend available")

        buffer = io.BytesIO()
        sf.write(buffer, samples, sample_rate, format="MP3")
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=kokoro-audio.mp3"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    """Health check — also warms up the model."""
    pipe = init_pipeline()
    return {
        "status": "ok" if pipe else "degraded",
        "backend": KOKORO_BACKEND,
        "voices_loaded": len(VOICES),
        "model_dir": MODEL_DIR,
        "model_exists": os.path.exists(MODEL_PATH),
        "voices_exists": os.path.exists(VOICES_PATH),
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
