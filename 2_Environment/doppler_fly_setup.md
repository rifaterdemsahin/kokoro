# 🔐 Doppler & Fly.io Setup Guide

This guide explains how to correctly integrate Doppler for secret management with Fly.io for runtime deployment.

## The "Secret Injection" Concept

Doppler manages your environment variables and secrets securely. However, running `doppler run -- fly deploy` **only** provides those secrets to the build process (e.g., if your Dockerfile needs a secret during the `RUN` step). 

It does **not** push those secrets to the live runtime environment of your Fly.io application.

## How to Sync Secrets to Fly.io

To make your Doppler secrets available to your running application on Fly.io, you must explicitly import them into the Fly secret vault.

### Command

```bash
doppler secrets download --no-file --format docker | flyctl secrets import -a <your-app-name>
```

**Example for this project:**
```bash
doppler secrets download --no-file --format docker | flyctl secrets import -a secondbrain-kokoro
```

### What this does:
1. `doppler secrets download --no-file --format docker` securely downloads your current environment's secrets (like `GEMINI_API_KEY`) and formats them as a list of `KEY=VALUE` pairs.
2. `| flyctl secrets import` pipes those key-value pairs directly into Fly.io.
3. Fly.io immediately creates a new release and performs a rolling restart of your application with the new secrets loaded into the environment variables.

## Best Practices
- **Do not commit `.env` files.** Use Doppler exclusively.
- Whenever you add a **new secret** in the Doppler dashboard (like an API Key or DB connection string), you **must** run the sync command above to update the Fly.io environment.
- Verify secrets are loaded by running `flyctl secrets list -a <your-app-name>`.
