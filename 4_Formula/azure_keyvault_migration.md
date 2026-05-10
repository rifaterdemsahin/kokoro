# 🧪 Formula: Azure Key Vault Migration Strategy

**Objective:** Safely transition secret management from Doppler to Azure Key Vault. This document outlines the rationale, pros/cons, and the step-by-step formula for migration.

---

## 1. Why Azure Key Vault? (Pros vs. Cons)

Before moving from Doppler to Azure Key Vault, it's important to understand the trade-offs:

### ✅ Pros
* **Enterprise Integration:** Native, seamless integration with the Azure ecosystem (Entra ID, Managed Identities, Azure Functions, Azure App Services).
* **Enhanced Security:** Offers Hardware Security Modules (HSMs), strict Role-Based Access Control (RBAC), and detailed audit logging natively through Azure Monitor.
* **Consolidated Billing & Governance:** Bundled into your existing Azure subscription, making enterprise compliance and cost tracking easier.
* **Automated Rotation:** Built-in support for rotating credentials automatically for supported Azure resources.

### ❌ Cons
* **Developer Experience (DX):** Doppler's CLI (`doppler run`) is extremely developer-friendly. Local development with Azure Key Vault requires Azure CLI logins and specific SDK code, which can be slightly more cumbersome.
* **Complexity:** Steeper learning curve. Setting up Entra ID (Azure AD) roles, Service Principals, and Access Policies is more complex than Doppler's UI.
* **Naming Restrictions:** Azure Key Vault secret names only support alphanumeric characters and dashes (`-`), not underscores (`_`). You will need to rename variables (e.g., `GEMINI_API_KEY` to `GEMINI-API-KEY`).
* **Cross-Cloud Friction:** Since this project is deployed on Fly.io (not Azure), you lose the benefit of Azure Managed Identities and must manage Service Principal credentials manually.

---

## 2. Migration Plan

### Phase 1: Preparation & Infrastructure
1. **Provision Azure Key Vault:** Create the Key Vault instance in your Azure Subscription.
2. **Setup Access Policies / RBAC:** Configure Entra ID roles. Assign "Key Vault Secrets Officer" to your developer account and "Key Vault Secrets User" to the application.
3. **Audit & Migrate Secrets:** Export all current secrets from Doppler (`doppler secrets download --format json`) and manually import them into Azure Key Vault, remembering to convert underscores to dashes.

### Phase 2: Code Modification (The Formula)
Update the Python backend (`main.py`) to fetch secrets directly from Azure Key Vault instead of relying on environment variables injected by Doppler.

**1. Install Azure SDKs:**
Add these to your `requirements.txt`:
```txt
azure-identity
azure-keyvault-secrets
```

**2. Python Implementation:**
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os

# 1. Provide the URL of your Azure Key Vault
KEY_VAULT_NAME = os.environ.get("KEY_VAULT_NAME", "your-default-kv-name")
KV_URI = f"https://{KEY_VAULT_NAME}.vault.azure.net"

# 2. DefaultAzureCredential supports local Azure CLI login and Service Principals in production
try:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=KV_URI, credential=credential)

    # 3. Fetching a secret (Note the dash instead of underscore)
    gemini_api_key = client.get_secret("GEMINI-API-KEY").value
    
except Exception as e:
    print(f"Failed to connect to Azure Key Vault: {e}")
    # Fallback for local testing if needed
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
```

### Phase 3: Local Development Strategy
Instead of `doppler run -- python main.py`, the new local workflow will be:
1. Authenticate locally using the Azure CLI: 
   ```bash
   az login
   ```
2. Set the environment variable for the vault name: 
   ```bash
   export KEY_VAULT_NAME="my-kokoro-kv"
   ```
3. Run the application: 
   ```bash
   python main.py
   ```
*(The `DefaultAzureCredential` will automatically use your `az login` context).*

### Phase 4: Production Deployment (Fly.io Integration)
Since Fly.io is outside of Azure, we cannot use Azure Managed Identities. We must use an Azure Service Principal.

1. **Create an Azure Service Principal** in Entra ID.
2. **Grant Access:** Give the Service Principal "Key Vault Secrets User" access to your Key Vault.
3. **Inject Credentials:** Save the Service Principal credentials as Fly.io secrets. `DefaultAzureCredential` will automatically detect these specific environment variables and authenticate.

```bash
flyctl secrets set \
  AZURE_CLIENT_ID="your-service-principal-id" \
  AZURE_TENANT_ID="your-tenant-id" \
  AZURE_CLIENT_SECRET="your-service-principal-secret" \
  KEY_VAULT_NAME="my-kokoro-kv" \
  -a secondbrain-kokoro
```

---

## 3. The Golden Rules for Azure Key Vault
1. **Never Hardcode Credentials:** Use `DefaultAzureCredential` for a seamless transition between local dev (`az login`) and production (Service Principal).
2. **Memory Caching:** Fetch secrets once on application startup and cache them in memory. Do not fetch from the Key Vault on every request to avoid latency and API limits.
3. **Dash, Not Underscore:** Always remember the naming convention change (`FLY-API-TOKEN`, not `FLY_API_TOKEN`).
