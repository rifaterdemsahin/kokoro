#!/usr/bin/env python3
"""
Kokoro TTS Server — Fixed version with runtime model download.
"""

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import io
import os
import re
import urllib.request
import soundfile as sf
import tempfile
import asyncio
import edge_tts
import google.generativeai as genai
from google import genai as google_genai
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

app = FastAPI(title="Kokoro TTS Server")

# Browsers on GitHub Pages / Steam Deck need CORS to call /voices and /api/speak.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Azure Key Vault
KEY_VAULT_NAME = os.environ.get("KEY_VAULT_NAME", "dp-kv-deliverypilot")
KV_URI = f"https://{KEY_VAULT_NAME}.vault.azure.net"

try:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=KV_URI, credential=credential)
    gemini_api_key = client.get_secret("GEMINI-API-KEY-PRIMARY").value
except Exception as e:
    print(f"Failed to connect to Azure Key Vault: {e}")
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

# Configure Gemini
genai.configure(api_key=gemini_api_key)

# google-genai client for the Gemini TTS ("Test Google API") button.
# Uses the same key pulled from Key Vault / GEMINI_API_KEY above.
_google_genai_client = None

def get_google_genai_client():
    global _google_genai_client
    if _google_genai_client is None:
        _google_genai_client = google_genai.Client(api_key=gemini_api_key)
    return _google_genai_client

GOOGLE_TTS_MODEL = "gemini-3.1-flash-tts-preview"
GOOGLE_TTS_VOICES = {
    "Kore": "Firm",
    "Puck": "Upbeat",
    "Charon": "Informative",
    "Orus": "Firm",
    "Leda": "Youthful",
    "Fenrir": "Excitable",
}

def chunk_text_for_tts(text: str, max_chars: int = 1500) -> list[str]:
    """Splits long text into paragraph-aware chunks to avoid model cutoffs."""
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) <= max_chars:
            current += para + "\n\n"
        else:
            if current:
                chunks.append(current.strip())
            current = para + "\n\n"
    if current:
        chunks.append(current.strip())
    return chunks or [text]

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

with open("cost-comparison.html", "r") as f:
    HTML_COST_COMPARISON = f.read()

with open("chrome-extension.html", "r") as f:
    HTML_CHROME_EXTENSION = f.read()

# OpenAI default voice aliases -> Kokoro voices so extensions work out of the box
OPENAI_VOICE_MAP = {
    "alloy": "af_heart",
    "echo": "am_adam",
    "fable": "bf_emma",
    "onyx": "bm_george",
    "nova": "af_bella",
    "shimmer": "af_nicole",
}

# ── Endpoints ───────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_UI

@app.get("/cost-comparison.html", response_class=HTMLResponse)
def cost_comparison():
    return HTML_COST_COMPARISON

@app.get("/chrome-extension.html", response_class=HTMLResponse)
@app.get("/chrome-extension", response_class=HTMLResponse)
def chrome_extension_guide():
    return HTML_CHROME_EXTENSION

@app.get("/chrome-extension-reader.jpg", include_in_schema=False)
def chrome_extension_screenshot():
    from fastapi.responses import FileResponse
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "3_Simulation", "chrome-extension-reader.jpg")
    return FileResponse(path, media_type="image/jpeg")

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

@app.post("/tts-google")
async def tts_google(
    text: str = Form(..., max_length=5000),
    voice: str = Form("Kore"),
):
    """Generate speech via Google's Gemini TTS (google-genai SDK) as an alternative
    engine to self-hosted Kokoro. Reuses the same Gemini API key as /enhance."""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    if voice not in GOOGLE_TTS_VOICES:
        raise HTTPException(status_code=400, detail=f"Unknown Google voice: {voice}")

    try:
        import base64
        import wave

        client = get_google_genai_client()
        chunks = chunk_text_for_tts(text)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)
            for chunk in chunks:
                interaction = client.interactions.create(
                    model=GOOGLE_TTS_MODEL,
                    input=chunk,
                    response_format={"type": "audio"},
                    generation_config={"speech_config": [{"voice": voice}]},
                )
                pcm = base64.b64decode(interaction.output_audio.data)
                wav_file.writeframes(pcm)

        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=google-tts-audio.wav"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Google TTS error: {e}")


class SpeakRequest(BaseModel):
    text: str = Field(..., max_length=5000, description="Text to convert to speech")
    voice: str = Field("af_heart", description="Voice ID (see GET /voices)")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Speech speed multiplier")


@app.post("/api/speak", summary="Text-to-speech via JSON")
async def api_speak(body: SpeakRequest):
    """
    Send JSON with `text`, optional `voice` and `speed`.
    Returns an MP3 audio stream.

    Example:
        curl -X POST http://localhost:8080/api/speak \\
          -H "Content-Type: application/json" \\
          -d '{"text": "Hello world", "voice": "af_heart", "speed": 1.0}' \\
          --output hello.mp3
    """
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")
    if body.voice not in VOICES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown voice '{body.voice}'. Call GET /voices for the list."
        )

    try:
        if body.voice.startswith("tr-"):
            rate_str = (
                f"+{int((body.speed - 1.0) * 100)}%"
                if body.speed >= 1.0
                else f"{int((body.speed - 1.0) * 100)}%"
            )
            communicate = edge_tts.Communicate(body.text, body.voice, rate=rate_str)
            buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])
            buffer.seek(0)
            return StreamingResponse(buffer, media_type="audio/mpeg",
                                     headers={"Content-Disposition": "attachment; filename=speech.mp3"})

        pipe = init_pipeline()
        if pipe is None:
            raise HTTPException(status_code=503, detail="TTS engine failed to load. Check server logs.")

        if KOKORO_BACKEND == "onnx":
            samples, sample_rate = pipe.create(body.text, voice=body.voice, speed=body.speed)
        elif KOKORO_BACKEND == "torch":
            for _, _, audio in pipe(body.text, voice=body.voice, speed=body.speed):
                samples = audio
                sample_rate = 24000
                break
        else:
            raise HTTPException(status_code=503, detail="No TTS backend available")

        buffer = io.BytesIO()
        sf.write(buffer, samples, sample_rate, format="MP3")
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="audio/mpeg",
                                 headers={"Content-Disposition": "attachment; filename=speech.mp3"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class OpenAISpeechRequest(BaseModel):
    model: str = Field("kokoro", description="Model ID (kokoro, tts-1, tts-1-hd)")
    input: str = Field(..., max_length=5000, description="Text to convert to speech")
    voice: str = Field("af_heart", description="Kokoro or OpenAI voice ID")
    response_format: str = Field("mp3", description="Audio format: mp3, wav, opus, flac")
    speed: float = Field(1.0, ge=0.25, le=4.0, description="Speech speed multiplier")


@app.get("/v1/models", summary="OpenAI-compatible models list")
def v1_models():
    return {
        "object": "list",
        "data": [
            {"id": "kokoro", "object": "model", "created": 1686935002, "owned_by": "kokoro"},
            {"id": "tts-1", "object": "model", "created": 1686935002, "owned_by": "kokoro"},
            {"id": "tts-1-hd", "object": "model", "created": 1686935002, "owned_by": "kokoro"},
        ],
    }


@app.get("/v1/audio/voices", summary="OpenAI/Kokoro-FastAPI compatible voices list")
def v1_voices():
    return {"voices": list(VOICES.keys())}


@app.post("/v1/audio/speech", summary="OpenAI-compatible Text-to-Speech")
async def v1_audio_speech(body: OpenAISpeechRequest):
    if not body.input.strip():
        raise HTTPException(status_code=400, detail="input must not be empty")

    voice = OPENAI_VOICE_MAP.get(body.voice, body.voice)
    if voice not in VOICES:
        voice = "af_heart"

    speed = max(0.5, min(2.0, body.speed))
    fmt = body.response_format.lower()
    format_map = {
        "mp3": ("MP3", "audio/mpeg", "mp3"),
        "wav": ("WAV", "audio/wav", "wav"),
        "flac": ("FLAC", "audio/flac", "flac"),
        "opus": ("OGG", "audio/ogg", "ogg"),
    }
    sf_fmt, media_type, ext = format_map.get(fmt, ("MP3", "audio/mpeg", "mp3"))

    try:
        if voice.startswith("tr-"):
            rate_str = f"+{int((speed - 1.0) * 100)}%" if speed >= 1.0 else f"{int((speed - 1.0) * 100)}%"
            communicate = edge_tts.Communicate(body.input, voice, rate=rate_str)
            buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])
            buffer.seek(0)
            return StreamingResponse(
                buffer,
                media_type="audio/mpeg",
                headers={"Content-Disposition": "attachment; filename=speech.mp3"},
            )

        pipe = init_pipeline()
        if pipe is None:
            raise HTTPException(status_code=503, detail="TTS engine failed to load. Check server logs.")

        if KOKORO_BACKEND == "onnx":
            samples, sample_rate = pipe.create(body.input, voice=voice, speed=speed)
        elif KOKORO_BACKEND == "torch":
            for _, _, audio in pipe(body.input, voice=voice, speed=speed):
                samples = audio
                sample_rate = 24000
                break
        else:
            raise HTTPException(status_code=503, detail="No TTS backend available")

        buffer = io.BytesIO()
        sf.write(buffer, samples, sample_rate, format=sf_fmt)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename=speech.{ext}"},
        )
    except HTTPException:
        raise
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
