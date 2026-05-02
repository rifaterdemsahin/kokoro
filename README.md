```button
name 🗄️ Move to Archive
type command
action Shell commands: Execute: Archive Current File
```

# Kokoro TTS Deployment: Comprehensive Overview

This document consolidates all information regarding the Kokoro Text-to-Speech (TTS) deployment across different environments (Cloud and Local) and its integration with the Second Brain ecosystem.

---

## 1. Cloud Deployment (Fly.io)
**Status**: Operational
**URL**: [https://secondbrain-kokoro.fly.dev/](https://secondbrain-kokoro.fly.dev/)

### Architecture
- **App Name**: `secondbrain-kokoro`
- **Region**: London (`lhr`)
- **Backend**: FastAPI + `kokoro-onnx` (ONNX Runtime)
- **Specs**: 2 shared vCPUs, 2 GB RAM
- **Features**: Auto-stop when idle, auto-start on request.

### Usage
- **Web UI**: Access via the live URL for a dark-mode scratchpad.
- **API Endpoint**: `POST https://secondbrain-kokoro.fly.dev/tts`
- **Costs**: ~$2/month (primarily for the shared IPv4 address).

---

## 2. Local Deployment (Proxmox / Docker)
**Status**: Functional (Integrated with Open WebUI)
**Location**: Proxmox Host

### Configuration
- **Container Name**: `kokoro-tts`
- **Image**: `ghcr.io/remsky/kokoro-fastapi-cpu:latest`
- **Network**: Host mode (`--network host`)
- **Port**: `8880`

### Host Maintenance
- **Disk Space**: Host disk resized to **60GB** to accommodate the ~2GB Kokoro image and other AI models.
- **Cleanup**: Removed `4_Archieve/imported-posts/media-library` to free initial space.

---

## 3. Open WebUI Integration
Kokoro acts as a local OpenAI-compatible TTS provider for Open WebUI.

### Connection Settings
- **Protocol**: OpenAI TTS
- **API Base URL**: `http://localhost:8880/v1`
- **Model**: `kokoro`
- **Default Voice**: `af_heart`

---

## 4. Diagnosis & Troubleshooting
### Common Issues (Resolved 2026-04-26)
1. **Redundant Env Vars**: `ENABLE_TTS=True` is unrecognized by Open WebUI and was removed from container configs to avoid confusion.
2. **Client-side vs Server-side**: Open WebUI may default to "Browser" TTS (WASM). Ensure "OpenAI" is selected in **Admin Panel > Settings > Audio** to use the Kokoro container.
3. **Cache Empty**: If `/app/backend/data/cache/audio/speech/` is empty, no server-side requests are hitting the container.

### Verification Commands
```bash
# Check local API health
curl http://localhost:8880/v1/models

# List available voices on Fly.io
curl https://secondbrain-kokoro.fly.dev/voices | python3 -m json.tool
```

---

## 5. Maintenance Commands
- **Check Status**: `flyctl status -a secondbrain-kokoro`
- **View Logs**: `flyctl logs -a secondbrain-kokoro`
- **Restart**: `flyctl restart -a secondbrain-kokoro`

---
