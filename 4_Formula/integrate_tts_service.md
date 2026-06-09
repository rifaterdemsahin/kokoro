# 🔌 How to Integrate the Kokoro TTS Service into Another App

**Service URL:** `https://secondbrain-kokoro.fly.dev`  
**Endpoint:** `POST /api/speak`  
**Returns:** MP3 audio binary (`audio/mpeg`)

---

## 1. One-Liner Mental Model

```
Your App  →  POST /api/speak  { text, voice, speed }  →  MP3 bytes
```

No auth required. No API key. Fire and forget.

---

## 2. Request Schema

```json
{
  "text":  "The text you want spoken. Max 5000 characters.",
  "voice": "af_heart",
  "speed": 1.0
}
```

| Field | Required | Default | Options |
|-------|----------|---------|---------|
| `text` | ✅ | — | Any string, max 5000 chars |
| `voice` | ❌ | `af_heart` | See voice table below |
| `speed` | ❌ | `1.0` | `0.5` – `2.0` |

### Voice IDs

| ID | Description | Engine |
|----|-------------|--------|
| `af_heart` | American Female — Heart | Kokoro ONNX |
| `af_bella` | American Female — Bella | Kokoro ONNX |
| `af_nicole` | American Female — Nicole | Kokoro ONNX |
| `am_adam` | American Male — Adam | Kokoro ONNX |
| `am_michael` | American Male — Michael | Kokoro ONNX |
| `bf_emma` | British Female — Emma | Kokoro ONNX |
| `bm_george` | British Male — George | Kokoro ONNX |
| `tr-TR-EmelNeural` | Turkish Female | Edge-TTS |
| `tr-TR-AhmetNeural` | Turkish Male | Edge-TTS |

Live list: `GET https://secondbrain-kokoro.fly.dev/voices`

---

## 3. Code Recipes

### Python (requests)

```python
import requests

def text_to_speech(text: str, voice: str = "af_heart", speed: float = 1.0) -> bytes:
    response = requests.post(
        "https://secondbrain-kokoro.fly.dev/api/speak",
        json={"text": text, "voice": voice, "speed": speed},
        timeout=30,
    )
    response.raise_for_status()
    return response.content  # raw MP3 bytes

# Save to file
audio = text_to_speech("Welcome to my app.")
with open("output.mp3", "wb") as f:
    f.write(audio)
```

### Python (httpx — async)

```python
import httpx

async def text_to_speech(text: str, voice: str = "af_heart") -> bytes:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://secondbrain-kokoro.fly.dev/api/speak",
            json={"text": text, "voice": voice},
        )
        r.raise_for_status()
        return r.content
```

### JavaScript / Node.js

```js
async function textToSpeech(text, voice = "af_heart", speed = 1.0) {
  const res = await fetch("https://secondbrain-kokoro.fly.dev/api/speak", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice, speed }),
  });
  if (!res.ok) throw new Error(`TTS failed: ${res.status}`);
  return Buffer.from(await res.arrayBuffer()); // MP3 buffer
}

// Save to file (Node)
const fs = require("fs");
const audio = await textToSpeech("Hello from my app.");
fs.writeFileSync("output.mp3", audio);
```

### Browser (play inline)

```js
async function speakInBrowser(text, voice = "af_heart") {
  const res = await fetch("https://secondbrain-kokoro.fly.dev/api/speak", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice }),
  });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.play();
}
```

### curl

```bash
curl -X POST https://secondbrain-kokoro.fly.dev/api/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice": "af_heart", "speed": 1.0}' \
  --output speech.mp3
```

---

## 4. How to Prompt an AI Agent to Use This Service

If your app uses an LLM or AI agent, paste this block into its **system prompt**:

```
## Text-to-Speech Tool

You have access to a TTS service. When the user asks you to speak, read aloud,
generate audio, or produce an MP3, call this service:

  POST https://secondbrain-kokoro.fly.dev/api/speak
  Content-Type: application/json
  Body: { "text": "<text to speak>", "voice": "<voice_id>", "speed": 1.0 }

Available voices: af_heart (default), af_bella, af_nicole, am_adam, am_michael,
bf_emma, bm_george, tr-TR-EmelNeural (Turkish), tr-TR-AhmetNeural (Turkish).

Rules:
- Always use the language that matches the text (tr-TR voices for Turkish text).
- Default voice is af_heart unless the user specifies gender/accent.
- Keep text under 5000 characters per request; split longer content.
- The response is raw MP3 binary — save it as a .mp3 file or play it directly.
- If the service returns HTTP 503, it is warming up (cold start ~5s); retry once.
```

### As an OpenAI-style Tool Definition

```json
{
  "type": "function",
  "function": {
    "name": "text_to_speech",
    "description": "Convert text to an MP3 audio file using the Kokoro TTS service. Use when the user wants audio, narration, or spoken output.",
    "parameters": {
      "type": "object",
      "properties": {
        "text": {
          "type": "string",
          "description": "The text to convert to speech. Max 5000 characters."
        },
        "voice": {
          "type": "string",
          "enum": ["af_heart","af_bella","af_nicole","am_adam","am_michael","bf_emma","bm_george","tr-TR-EmelNeural","tr-TR-AhmetNeural"],
          "description": "Voice ID. Use tr-TR voices for Turkish text. Default: af_heart."
        },
        "speed": {
          "type": "number",
          "description": "Speech speed multiplier. Range 0.5 (slow) to 2.0 (fast). Default: 1.0."
        }
      },
      "required": ["text"]
    }
  }
}
```

### Python tool handler (to wire the tool call to the actual request)

```python
import requests

def text_to_speech(text: str, voice: str = "af_heart", speed: float = 1.0) -> str:
    """Called by the agent when it invokes the text_to_speech tool."""
    r = requests.post(
        "https://secondbrain-kokoro.fly.dev/api/speak",
        json={"text": text, "voice": voice, "speed": speed},
        timeout=30,
    )
    r.raise_for_status()
    path = f"/tmp/speech_{hash(text) % 10000}.mp3"
    with open(path, "wb") as f:
        f.write(r.content)
    return f"Audio saved to {path}"
```

---

## 5. Error Handling Reference

| HTTP code | Meaning | Action |
|-----------|---------|--------|
| `200` | Success — body is MP3 | Save / play |
| `400` | Bad request (empty text, unknown voice) | Fix the request |
| `422` | Validation error (speed out of range, missing field) | Check field types |
| `503` | TTS engine not ready | Wait 5s, retry once |
| `500` | Unexpected server error | Log and retry |

```python
import time, requests

def safe_tts(text, retries=2):
    for attempt in range(retries):
        r = requests.post(
            "https://secondbrain-kokoro.fly.dev/api/speak",
            json={"text": text},
            timeout=30,
        )
        if r.status_code == 503 and attempt < retries - 1:
            time.sleep(5)
            continue
        r.raise_for_status()
        return r.content
```

---

## 6. Cold Start Warning

The Fly.io machine auto-stops when idle. The **first request after idle adds ~3–5 seconds**.

To pre-warm before your app's session starts:

```python
import requests
requests.post(
    "https://secondbrain-kokoro.fly.dev/api/speak",
    json={"text": "warmup", "voice": "af_heart"},
    timeout=15,
)
```

Or send a health ping first and wait for `status: ok`:

```python
import requests, time

def wait_for_warm(max_wait=15):
    for _ in range(max_wait):
        try:
            r = requests.get("https://secondbrain-kokoro.fly.dev/health", timeout=3)
            if r.json().get("status") == "ok":
                return True
        except Exception:
            pass
        time.sleep(1)
    return False
```

---

## 7. Enhance Text Before Speaking (Optional)

If your text is rough or unscripted, call `/enhance` first to let Gemini polish it:

```python
def enhance_then_speak(text: str, lang: str = "en") -> bytes:
    # Step 1 — polish
    enhanced = requests.post(
        "https://secondbrain-kokoro.fly.dev/enhance",
        data={"text": text, "lang": lang},
        timeout=15,
    ).json()["text"]

    # Step 2 — speak
    return requests.post(
        "https://secondbrain-kokoro.fly.dev/api/speak",
        json={"text": enhanced},
        timeout=30,
    ).content
```

---

## 8. Quick-Reference Cheat Sheet

```
SERVICE   https://secondbrain-kokoro.fly.dev

SPEAK     POST /api/speak
          Body (JSON): { text*, voice, speed }
          Returns: audio/mpeg MP3

VOICES    GET  /voices
          Returns: JSON list of all voice IDs

ENHANCE   POST /enhance
          Body (form): text=..., lang=en|tr
          Returns: { text: "polished text" }

HEALTH    GET  /health
          Returns: { status, backend, voices_loaded }

DOCS      GET  /docs   (Swagger UI — interactive)
```
