#!/usr/bin/env python3
"""
Kokoro TTS Server — Fixed version with runtime model download.
"""

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import os
import re
import urllib.request
import soundfile as sf
import tempfile
import asyncio
import edge_tts
import google.generativeai as genai
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

app = FastAPI(title="Kokoro TTS Server")

# Configure Azure Key Vault
KEY_VAULT_NAME = os.environ.get("KEY_VAULT_NAME", "secondbrain-kokoro-kv")
KV_URI = f"https://{KEY_VAULT_NAME}.vault.azure.net"

try:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=KV_URI, credential=credential)
    gemini_api_key = client.get_secret("GEMINI-API-KEY").value
except Exception as e:
    print(f"Failed to connect to Azure Key Vault: {e}")
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

# Configure Gemini
genai.configure(api_key=gemini_api_key)

# ── Model Download ──────────────────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "kokoro-v1.0.onnx")
VOICES_PATH = os.path.join(MODEL_DIR, "voices-v1.0.bin")

def download_file(url: str, dest: str):
    if os.path.exists(dest):
        return
    print(f"[Kokoro] Downloading {os.path.basename(dest)}...")
    urllib.request.urlretrieve(url, dest)
    print(f"[Kokoro] Saved to {dest}")

def ensure_models():
    download_file(MODEL_URL, MODEL_PATH)
    download_file(VOICES_URL, VOICES_PATH)

# ── TTS Backend ─────────────────────────────────────────────────────
KOKORO_BACKEND = None
pipeline = None

def init_pipeline():
    global pipeline, KOKORO_BACKEND
    if pipeline is not None:
        return pipeline

    try:
        from kokoro_onnx import Kokoro
        ensure_models()
        pipeline = Kokoro(MODEL_PATH, VOICES_PATH)
        KOKORO_BACKEND = "onnx"
        print(f"[Kokoro] Loaded ONNX backend with {len(pipeline.voices)} voices")
        return pipeline
    except Exception as e:
        print(f"[Kokoro] ONNX failed: {e}")

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
    "tr-TR-AhmetNeural": {"name": "TR Ahmet — Male (TR)", "gender": "male", "lang": "tr-TR"},
    "tr-TR-EmelNeural": {"name": "TR Emel — Female (TR)", "gender": "female", "lang": "tr-TR"},
}

with open("index.html", "r") as f:
    HTML_UI = f.read()

# ── Endpoints ───────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_UI

@app.get("/voices")
def list_voices():
    return {"voices": VOICES}

@app.post("/enhance")
async def enhance(text: str = Form(...), lang: str = Form("en")):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
        
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = (
            f"Please enhance the following text for a voiceover/TTS generation. "
            f"Make it sound natural, conversational, and add appropriate punctuation for pacing. "
            f"Do NOT use markdown formatting such as asterisks, bold, italics, or underscores. "
            f"Use plain text only. "
            f"The language is {'Turkish' if lang == 'tr' else 'English'}. "
            f"Respond ONLY with the enhanced text, without any quotes or explanations.\n\nText: {text}"
        )
        print(f"[DEBUG] Enhance Prompt: {prompt}")
        
        response = model.generate_content(prompt)
        enhanced_text = response.text.strip()
        
        # Strip any remaining markdown asterisks/underscores to ensure TTS-friendliness
        enhanced_text = re.sub(r'(\*{1,2}|_{1,2})(.*?)\1', r'\2', enhanced_text)
        enhanced_text = enhanced_text.replace('*', '')
        
        return {"text": enhanced_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts")
async def tts(
    text: str = Form(..., max_length=5000),
    voice: str = Form("af_heart"),
    speed: float = Form(1.0),
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    if voice not in VOICES:
        raise HTTPException(status_code=400, detail=f"Unknown voice: {voice}")

    try:
        # Generate a meaningful filename using Gemini
        filename = "kokoro-audio.mp3"
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            name_prompt = f"Generate a 2-3 word slug (lowercase, hyphen-separated, no extension) summarizing this text for a filename. Respond ONLY with the slug.\n\nText: {text[:500]}"
            res = model.generate_content(name_prompt)
            slug = res.text.strip().lower().replace(' ', '-')
            import re
            slug = re.sub(r'[^a-z0-9\-]', '', slug)
            if slug:
                filename = f"{slug}.mp3"
        except Exception as e:
            print(f"[DEBUG] Filename generation failed: {e}")

        # Edge-TTS logic for Turkish
        if voice.startswith("tr-"):
            rate_str = f"+{int((speed - 1.0) * 100)}%" if speed >= 1.0 else f"{int((speed - 1.0) * 100)}%"
            communicate = edge_tts.Communicate(text, voice, rate=rate_str)
            
            buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])
                    
            buffer.seek(0)
            return StreamingResponse(
                buffer,
                media_type="audio/mpeg",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        # Kokoro logic
        pipe = init_pipeline()
        if pipe is None:
            raise HTTPException(
                status_code=503,
                detail="TTS engine failed to load. Check server logs."
            )

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
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
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
