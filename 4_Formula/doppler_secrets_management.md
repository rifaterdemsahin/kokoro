# 🧪 Formula: Doppler Secrets Management

**Objective:** Safely manage, synchronize, and deploy sensitive credentials (like `GEMINI_API_KEY` and `FLY_API_TOKEN`) across environments without using local `.env` files.

---

## 1. The Visual Proof (Simulation)
In the `3_Simulation` folder, we have documented the manual entry of secrets via the Doppler UI: `doppler _secrets_manually_saved.png`. This serves as the source of truth for our staging (`stg`) or production (`prd`) environment variables.

---

## 2. Step-by-Step Logic

### Step A: Setup & Authentication
Always bind your current workspace to the correct Doppler project and environment configuration.
```bash
# Login to Doppler CLI
doppler login

# Bind the current directory to the 'kokoro' project and 'stg' (Staging) config
doppler setup -p kokoro -c stg
```

### Step B: Local Development
When testing the TTS server locally, you never need to download the secrets to a physical file. Instead, inject them dynamically:
```bash
doppler run -- python main.py
```
*Why this works:* Doppler momentarily injects the secrets (like your Gemini API Key) into the process environment variables and removes them when the process terminates.

### Step C: Deploying the Application Build
To allow Fly.io's build agent (Depot) to use secrets if required during the `Dockerfile` build step:
```bash
doppler run -- fly deploy
```

### Step D: Synchronizing Runtime Secrets to Fly.io
Fly.io requires runtime variables to be stored in its own secure vault. Whenever you manually save a new secret in the Doppler UI (like the one shown in the `3_Simulation` screenshot), you must sync it to the Fly machine:

```bash
doppler secrets download --no-file --format docker | flyctl secrets import -a secondbrain-kokoro
```

---

## 3. The Golden Rules
1. **No `.env` files allowed:** Never hardcode secrets in source code or `.env` templates.
2. **Dashboard First:** Create and save secrets manually in the Doppler Web UI first.
3. **Sync immediately:** Run the Step D sync command immediately after updating the dashboard.
