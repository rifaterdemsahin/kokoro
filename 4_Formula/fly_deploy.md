# 🚀 Fly.io Deploy — Formula

## App Details

| Key | Value |
|-----|-------|
| **App name** | `secondbrain-kokoro` |
| **Live URL** | https://secondbrain-kokoro.fly.dev/ |
| **Region** | London (`lhr`) |
| **Specs** | 2 shared vCPUs, 2 GB RAM |
| **Config** | `fly.toml` (root of repo) |

---

## Deploy Command

Run from the project root (`/Users/rifaterdemsahin/Projects/kokoro`):

```bash
fly deploy
```

This builds the Docker image locally, pushes it to Fly.io's registry, and rolls it out. Takes ~3–5 minutes (longer on first run due to model downloads).

---

## Full Deploy Workflow

```bash
# 1. Make code changes

# 2. Commit and push to GitHub
git add .
git commit -m "your message"
git push origin main

# 3. Deploy to Fly.io
fly deploy

# 4. Verify deployment
curl https://secondbrain-kokoro.fly.dev/health
```

---

## Check Logs

```bash
fly logs
fly logs --app secondbrain-kokoro
```

## Check Status

```bash
fly status
fly status --app secondbrain-kokoro
```

## SSH into the Machine

```bash
fly ssh console
```

---

## Secrets Management

Secrets are stored in Fly.io (sourced from Doppler). Never commit secrets to git.

```bash
# View current secrets (keys only, not values)
fly secrets list

# Set a secret manually
fly secrets set GEMINI_API_KEY=your-key

# Import from Doppler
doppler secrets download --no-file --format docker > .env
fly secrets import < .env
rm .env
```

---

## Scaling

```bash
# Scale memory
fly scale memory 2048

# Scale VM count
fly scale count 1

# View current scale
fly scale show
```

---

## Auto-stop Behaviour

The app is configured with `auto_stop_machines = 'stop'` and `min_machines_running = 0`.
This means the machine stops when idle and cold-starts on the next request (~2–5s delay).

To keep it always warm:
```bash
fly scale count 1
# then in fly.toml: min_machines_running = 1
fly deploy
```

---

## Install fly CLI

```bash
# macOS (Homebrew)
brew install flyctl

# Or via install script
curl -L https://fly.io/install.sh | sh
```

Then authenticate:
```bash
fly auth login
```
