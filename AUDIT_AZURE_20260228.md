# Crown2026 — Azure App Service Audit
**Date:** 2026-02-28  
**Auditor:** GitHub Copilot (hard-facts, no-assumptions mode)  
**Subscription:** `4ef0ba4b-4810-48d4-b3fe-953a9708953a` — "CROWN Christian School Management"  
**Tenant:** `08597807-7a79-490b-87e5-83ae3e9d4b15`  
**Auth context:** JMegahan@msn.com  

---

## 1. Resources Under Audit

| Resource | Name | RG | Location |
|---|---|---|---|
| App Service (prod) | `crown-api-prod` | `crown-rg` | East US |
| App Service (dev) | `crown-api-dev` | `crown-rg` | East US |
| Container Registry | `crownregistry` | (same sub) | eastus |
| Static Web App (frontend) | crown-dash (SWA) | unknown | — |

All names sourced from deploy workflow `env:` blocks, not guessed.

---

## 2. Deployment Mechanism

**How deploy works (verified from `.github/workflows/deploy-prod.yml`):**
- Trigger: `push` to tag matching `prod-deploy-*`
- Mechanism: Docker container → Azure Container Registry → App Service pulls image
- Auth: `azure/login@v1` using `secrets.AZURE_CREDENTIALS` (service principal credentials stored as GitHub Actions secret)
- BUILD_SHA: set as App Service app setting AND baked into `backend/crown_api/build_info.py` inside the image
- Guard: tag name check (`prod-deploy-*` prefix), SHA presence check, AcrPull managed identity check

**Prod deploy trigger history (tags, newest first):**
```
prod-deploy-2026-02-27          ← currently deployed
prod-deploy-certify-2026-02-24
prod-deploy-tag-only-2026-02-21
prod-deploy-2026-02-24-1952
prod-deploy-2026-02-24-0545
prod-deploy-2026-02-23-1845
prod-deploy-2026-02-23-1816
prod-deploy-2026-02-23-1809
prod-deploy-2026-02-23-1750
prod-deploy-2026-02-22-1439
```

---

## 3. Deployed SHA vs Repository HEAD

| Item | SHA |
|---|---|
| `origin/main` HEAD | `61e67163fad2737c875f16c1a4145db5f7b077e3` |
| Prod `BUILD_SHA` (app setting) | `cfa5b4a0de90cbe0e7bad2717adf015453bd98f5` |
| Prod Docker image tag | `cfa5b4a0de90cbe0e7bad2717adf015453bd98f5` |
| Live `/api/health/` `build_sha` | `cfa5b4a0de90cbe0e7bad2717adf015453bd98f5` |

**All three prod SHA sources match each other — the SHA-proving chain is intact.**

**FINDING — Deployment Lag:** `cfa5b4a0` is commit "feat: admissions move_stage() service with guarded FSM (#443)".  
`origin/main` HEAD `61e67163` is "feat: Finance Setup Wizard (CrownMagus) — year-locked financial canon (#491)".  
**46 commits on `origin/main` are NOT deployed to prod.**

```
git rev-list --count cfa5b4a0de90cbe0e7bad2717adf015453bd98f5..origin/main
→ 46
```

The `PROD_DEPLOY_TAG` app setting value: `prod-deploy-2026-02-27`.  
The latest prod tag is `prod-deploy-2026-02-27`, dated 2026-02-27. The audit runs on 2026-02-28.

---

## 4. Live Health Check

```
GET https://crown-api-prod.azurewebsites.net/api/health/
→ HTTP 200

{
  "ok": true,
  "status": "ok",
  "demo_mode": false,
  "build_sha": "cfa5b4a0de90cbe0e7bad2717adf015453bd98f5",
  "prod_deploy_tag": "prod-deploy-2026-02-27",
  "env": "prod",
  "build_time_utc": "2026-02-28T20:25:51.294340+00:00",
  "version": "crown-0.3.0",
  "db": "ok"
}
```

```
GET https://crown-api-prod.azurewebsites.net/api/integrity/
→ HTTP 200

{
  "ok": true,
  "build_sha": "cfa5b4a0de90cbe0e7bad2717adf015453bd98f5",
  "github_commit_url": "https://github.com/tcmegahan/Crown2026/commit/cfa5b4a0...",
  "env": "prod",
  "version": "crown-0.3.0",
  "prod_deploy_tag": "prod-deploy-2026-02-27",
  "required_checks": [
    "changes", "demo-proof-static", "demo-surface-static-gate",
    "lockdown-gate", "meta-check-job-if", "phase1-contract",
    "phase3-runtime-proof", "proof-ceremony", "pytest",
    "rc-promotion-gate", "spine-audit", "test", "verify-immutable-tags"
  ],
  "meta_gates": [
    {"id": "no-job-level-pr-if", ...},
    {"id": "no-unquoted-step-name-colon", ...}
  ]
}
```

**FINDING — Integrity/Protection Gap:** The `/api/integrity/` endpoint lists 13 `required_checks` that the *app* believes are enforced. Per the GitHub audit (`AUDIT_GITHUB_20260228.md`), `required_status_checks` in branch protection is **null** — none of these checks actually block a merge. The app self-reports enforcement that does not exist at the repository layer.

---

## 5. App Service Configuration — Prod

```
az webapp show -g crown-rg -n crown-api-prod (selected fields)

"state": "Running"
"kind": "app,linux,container"
"httpsOnly": true                   ✓
"minTlsVersion": "1.2"              ✓
"ftpsState": "FtpsOnly"             WARN (see below)
"http20Enabled": true               ✓
"remoteDebuggingEnabled": false     ✓
"alwaysOn": false                   ← FINDING (see below)
"scmType": "None"                   ✓ (deploy via ACR, not SCM push)
"linuxFxVersion": "DOCKER|crownregistry.azurecr.io/crown2026:cfa5b4a0..."
"httpLoggingEnabled": true          ✓
"detailedErrorLoggingEnabled": true ✓
"requestTracingEnabled": true       ✓
```

**F1 — `alwaysOn: false` in PROD.** The App Service will be unloaded after a period of inactivity, causing cold-start latency for the first request after idle. Production APIs should have `alwaysOn: true` to prevent cold starts. This requires at minimum a Basic (B1) App Service Plan.

**F2 — `ftpsState: "FtpsOnly"`.** FTPS is enabled (encrypted FTP). While not plain FTP, the preferred hardened state for a production API with no FTP usage is `"Disabled"`. This is a non-critical surface but represents an unnecessary attack surface.

---

## 6. App Settings Audit — Prod (names only)

Full list of app setting names on `crown-api-prod`:

```
DOCKER_REGISTRY_SERVER_URL
DOCKER_REGISTRY_SERVER_USERNAME
DOCKER_REGISTRY_SERVER_PASSWORD       ← FINDING
WEBSITES_ENABLE_APP_SERVICE_STORAGE
DEBUG
SECRET_KEY                            ← FINDING
ALLOWED_HOSTS
USE_POSTGRESQL
DB_NAME
DB_USER
DB_PASSWORD                           ← FINDING
DB_HOST
DB_PORT
CORS_ALLOWED_ORIGINS
APPINSIGHTS_INSTRUMENTATIONKEY        ✓
APPINSIGHTS_PROFILERENABLEDINSIGHTS
ApplicationInsightsAgent_EXTENSION_VERSION
AZURE_AD_DELEGATED_SCOPE
BUILD_SHA                             ✓
WEBSITE_HTTPLOGGING_RETENTION_DAYS
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS
RUN_MIGRATIONS
RUN_MIGRATE
RUN_DEV_BOOTSTRAP                     ← FINDING (name present in prod)
RUN_GOLDEN_PATH_BOOTSTRAP             ← FINDING (name present in prod)
CROWN_ENV
PROD_DEPLOY_TAG
ENVIRONMENT
```

**Non-secret indicator values confirmed:**
| Setting | Value |
|---|---|
| `DEBUG` | `False` ✓ |
| `DJANGO_DEBUG` | `0` ✓ |
| `BUILD_SHA` | `cfa5b4a0de90cbe0e7bad2717adf015453bd98f5` ✓ |
| `PROD_DEPLOY_TAG` | `prod-deploy-2026-02-27` ✓ |
| `CROWN_ENV` | `prod` ✓ |
| `ENVIRONMENT` | `prod` ✓ |
| `RUN_DEV_BOOTSTRAP` | `0` (disabled, but key present) |
| `RUN_GOLDEN_PATH_BOOTSTRAP` | `0` (disabled, but key present) |
| `CORS_ALLOWED_ORIGINS` | `https://crown-api-prod.azurewebsites.net` ← FINDING |

**F3 — `DOCKER_REGISTRY_SERVER_PASSWORD` in app settings.** ACR pull credentials (admin account username+password) are stored as plain text App Service app settings. Managed identity is configured (`SystemAssigned`, principalId `b63c61ef-6e24-4842-bca9-0f090353e849`) but ACR admin credentials are also present — dual authentication surface. If the ACR admin password rotates, the app breaks. If the app setting is leaked, registry write access is exposed.

**F4 — `SECRET_KEY` in app settings.** Django's `SECRET_KEY` is stored as a plain app setting rather than in Azure Key Vault with a Key Vault reference (`@Microsoft.KeyVault(...)`). A leaked app setting dump exposes Django session signing material.

**F5 — `DB_PASSWORD` in app settings.** PostgreSQL password stored as plain app setting rather than Key Vault reference. Same risk as F4.

**F6 — `CORS_ALLOWED_ORIGINS = "https://crown-api-prod.azurewebsites.net"`.** CORS allows only the API's own URL as an origin. This would block the SWA frontend dashboard (`crown-dash.azurestaticapps.net`) from making cross-origin requests to the prod API, unless CORS is also handled at a proxy/gateway layer or the SWA calls a different endpoint. Needs verification.

**F7 — `RUN_DEV_BOOTSTRAP` and `RUN_GOLDEN_PATH_BOOTSTRAP` keys exist in prod.** Both values are `0`, so they are currently disabled. However, these keys' presence in prod creates a one-variable-change blast radius where a misconfigured deploy could accidentally re-seed a production database. Name-only presence is a hygiene issue.

---

## 7. Managed Identity & ACR

**App Service managed identity:**
```
az webapp identity show -g crown-rg -n crown-api-prod
{
  "type": "SystemAssigned",
  "principalId": "b63c61ef-6e24-4842-bca9-0f090353e849",
  "tenantId": "08597807-..."
}
```
SystemAssigned identity is enabled. ✓

**ACR state:**
```
az acr show -n crownregistry
{
  "adminUserEnabled": true,            ← FINDING
  "publicNetworkAccess": "Enabled",    ← FINDING
  "sku": "Basic",                      ← NOTE
  "loginServer": "crownregistry.azurecr.io"
}
```

**F8 — ACR admin account enabled.** The registry admin account is active. Admin credentials are long-lived, cannot be scoped, and (per F3) are stored in app settings. The managed identity path (AcrPull role) exists but the admin path is also live. If admin creds rotate or leak, both the deploy pipeline AND the running app break or are compromised.

**F9 — ACR public network access enabled.** The registry is reachable from any IP on the public internet. On Basic SKU, private endpoint and network rules are not available (require Premium). Any valid credential (admin or service principal) can push or pull images from any network.

**F10 — ACR Basic SKU.** Basic SKU has no: content trust / image signing, geo-replication, private endpoints, or retention policies. A supply chain attack can silently replace an image tag; there is no cryptographic proof of image integrity on pull.

---

## 8. Network Access Restrictions

```
az webapp config access-restriction show -g crown-rg -n crown-api-prod
{
  "mainSiteRestrictions": null
}
```

**F11 — No IP access restrictions on prod App Service.** The production API (`crown-api-prod.azurewebsites.net`) is reachable from any IP address on the internet. There are no allowlist rules, no service tag restrictions, and no VNET integration. Any actor with valid authentication credentials can reach the API.

---

## 9. Deployment Slots

```
az webapp deployment slot list -g crown-rg -n crown-api-prod
→ []
```

**F12 — No deployment slots.** Zero-downtime deploys (blue-green/staging → prod swap) are not configured. Every deploy goes directly to the production slot. Rollback requires re-triggering the pipeline with a previous tag. During a container image pull on deploy, there is a window where the service may serve requests with the old image while the new one loads, or return errors if the new image fails container startup.

---

## 10. Dev App Service — Indicator Settings

```
az webapp config appsettings list -g crown-rg -n crown-api-dev (selected)

BUILD_SHA:    6f01abbdd0f88b18a00f0c39df86133bc7a4faa7
CROWN_ENV:    dev
DEBUG:        True
ENVIRONMENT:  dev
```

`DEBUG=True` on dev is expected. No `CROWN_DEMO_ALLOW_BYPASS_AUTH` or `CROWN_DEMO_MODE` keys present — the Demo Concierge environment variables (from PR #495) have not been deployed to dev yet (PR not merged).

Dev BUILD_SHA (`6f01abbdd0f`) does not match origin/main (`61e67163`) or prod (`cfa5b4a0`). Dev is on a third, unidentified deploy point.

---

## 11. Risk Register

| # | Finding | Severity | Reproduce Command | Impact |
|---|---|---|---|---|
| F1 | `alwaysOn: false` in prod | HIGH | `az webapp show -g crown-rg -n crown-api-prod --query siteConfig.alwaysOn` | Cold starts; unpredictable latency after idle period |
| F2 | `ftpsState: FtpsOnly` (not Disabled) | LOW | `az webapp show -g crown-rg -n crown-api-prod --query siteConfig.ftpsState` | Unnecessary attack surface |
| F3 | ACR admin password in app settings | CRITICAL | `az webapp config appsettings list -g crown-rg -n crown-api-prod --query "[?name=='DOCKER_REGISTRY_SERVER_PASSWORD']"` | Long-lived credential exposure; registry write access if leaked |
| F4 | `SECRET_KEY` in app settings | HIGH | (name listed in §6 output) | Django session compromise if settings dump leaked |
| F5 | `DB_PASSWORD` in app settings | HIGH | (name listed in §6 output) | Database credential exposure if settings dump leaked |
| F6 | CORS blocks SWA origin | HIGH | `az webapp config appsettings list -g crown-rg -n crown-api-prod --query "[?name=='CORS_ALLOWED_ORIGINS']"` | SWA frontend may be unable to call prod API; needs verification |
| F7 | Bootstrap keys present in prod | MEDIUM | `az webapp config appsettings list -g crown-rg -n crown-api-prod --query "[?name=='RUN_DEV_BOOTSTRAP']"` | One misconfigured deploy re-seeds prod DB |
| F8 | ACR admin account active | HIGH | `az acr show -n crownregistry --query adminUserEnabled` | Admin creds = registry write; can replace any image tag |
| F9 | ACR public network access | MEDIUM | `az acr show -n crownregistry --query publicNetworkAccess` | Registry reachable from any IP with valid credential |
| F10 | ACR Basic SKU (no signing) | MEDIUM | `az acr show -n crownregistry --query sku.name` | No image integrity guarantee; silent tag replacement possible |
| F11 | No IP access restrictions | MEDIUM | `az webapp config access-restriction show -g crown-rg -n crown-api-prod` | Prod API exposed to internet; relies on auth only |
| F12 | No deployment slots | MEDIUM | `az webapp deployment slot list -g crown-rg -n crown-api-prod` | Zero-downtime deploys impossible; no fast rollback |
| F13 | 46 commits undeployed to prod | INFO | `git rev-list --count cfa5b4a0..origin/main` | Origin/main is well ahead of prod; intentional lag or stale? |
| F14 | Integrity endpoint lists required_checks not enforced | HIGH | (see GitHub audit) | App self-reports governance that does not exist at repo layer |

---

## 12. Verified PASS Items

| Item | Verified |
|---|---|
| `httpsOnly: true` on prod | ✓ `az webapp show` |
| TLS 1.2 minimum | ✓ `minTlsVersion: "1.2"` |
| Remote debugging disabled | ✓ `remoteDebuggingEnabled: false` |
| `DEBUG=False`, `DJANGO_DEBUG=0` in prod | ✓ app settings query |
| `CROWN_ENV=prod`, `ENVIRONMENT=prod` | ✓ app settings query |
| `demo_mode: false` in live health response | ✓ `/api/health/` |
| No `CORS_ALLOW_ALL_ORIGINS` in prod | ✓ name not in app settings list |
| No demo bypass setting in prod | ✓ `CROWN_DEMO_ALLOW_BYPASS_AUTH` absent |
| BUILD_SHA consistent: app setting = image tag = health response | ✓ all three match `cfa5b4a0` |
| Managed identity (SystemAssigned) enabled | ✓ `az webapp identity show` |
| Application Insights instrumentation key present | ✓ `APPINSIGHTS_INSTRUMENTATIONKEY` in settings |
| HTTP logging, detailed errors, request tracing enabled | ✓ `az webapp show` siteConfig |
| Live `/api/health/` returns `{"ok":true, "db":"ok"}` | ✓ HTTP 200 |
| Live `/api/integrity/` returns `{"ok":true}` | ✓ HTTP 200 |
| Deploy triggered by signed tag (`prod-deploy-*`) not branch push | ✓ workflow trigger |
| Build guards present: tag format, SHA fullness, AcrPull verification | ✓ workflow steps |

---

## 13. Commands Used (Full Reproducing Set)

```bash
# 1. Account
az account show --query "{subscriptionId:id, name:name, tenantId:tenantId, state:state, user:user.name}" -o json

# 2. Prod App Service full config
az webapp show -g crown-rg -n crown-api-prod --query "{httpsOnly:httpsOnly, state:state, kind:kind, defaultHostName:defaultHostName, siteConfig:{minTlsVersion:siteConfig.minTlsVersion, ftpsState:siteConfig.ftpsState, http20Enabled:siteConfig.http20Enabled, linuxFxVersion:siteConfig.linuxFxVersion, alwaysOn:siteConfig.alwaysOn, remoteDebuggingEnabled:siteConfig.remoteDebuggingEnabled, httpLoggingEnabled:siteConfig.httpLoggingEnabled, detailedErrorLoggingEnabled:siteConfig.detailedErrorLoggingEnabled, requestTracingEnabled:siteConfig.requestTracingEnabled, scmType:siteConfig.scmType}}" -o json

# 3. Prod app setting NAMES
az webapp config appsettings list -g crown-rg -n crown-api-prod --query "[].name" -o json

# 4. Prod indicator values
az webapp config appsettings list -g crown-rg -n crown-api-prod --query "[?name=='BUILD_SHA' || name=='PROD_DEPLOY_TAG' || name=='DEBUG' || name=='DJANGO_DEBUG' || name=='CROWN_ENV' || name=='ENVIRONMENT' || name=='RUN_DEV_BOOTSTRAP' || name=='RUN_GOLDEN_PATH_BOOTSTRAP' || name=='CORS_ALLOWED_ORIGINS'].{name:name,value:value}" -o json

# 5. Managed identity
az webapp identity show -g crown-rg -n crown-api-prod --query "{type:type, principalId:principalId, tenantId:tenantId}" -o json

# 6. ACR state
az acr show -n crownregistry --query "{adminUserEnabled:adminUserEnabled, publicNetworkAccess:publicNetworkAccess, sku:sku.name, loginServer:loginServer}" -o json

# 7. Deployment slots
az webapp deployment slot list -g crown-rg -n crown-api-prod -o json

# 8. Network access restrictions
az webapp config access-restriction show -g crown-rg -n crown-api-prod --query mainSiteRestrictions -o json

# 9. Dev indicator settings
az webapp config appsettings list -g crown-rg -n crown-api-dev --query "[?name=='BUILD_SHA' || name=='CROWN_ENV' || name=='ENVIRONMENT' || name=='DEBUG'].{name:name,value:value}" -o json

# 10. SHA comparison
git rev-parse origin/main
# → 61e67163fad2737c875f16c1a4145db5f7b077e3
git rev-list --count cfa5b4a0de90cbe0e7bad2717adf015453bd98f5..origin/main
# → 46

# 11. Live health probes
Invoke-WebRequest https://crown-api-prod.azurewebsites.net/api/health/ -UseBasicParsing
Invoke-WebRequest https://crown-api-prod.azurewebsites.net/api/integrity/ -UseBasicParsing
```

---

## 14. Open Items Requiring Human Verification

1. **CORS vs SWA:** Verify whether the SWA is expected to call `crown-api-prod` directly or via a proxy. If direct, `CORS_ALLOWED_ORIGINS` must include the SWA URL or the frontend is broken in production.
2. **Dev SHA `6f01abbdd0f`:** Identify which commit is on dev and whether it matches a known RC branch or is stale.
3. **`AZURE_CREDENTIALS` secret in GitHub Actions:** Confirm this is a service principal with minimum-necessary permissions (not Owner/Contributor on the whole subscription).
4. **AcrPull role assignment:** Workflow guard checks for it, but confirm via `az role assignment list --assignee b63c61ef-... --scope $(az acr show -n crownregistry --query id -o tsv)` that the managed identity actually has AcrPull — and confirm whether the app is configured to *use* managed identity for image pull or is actually relying on the admin password in app settings.
5. **`alwaysOn: false`:** Confirm App Service Plan SKU. If on Basic or higher, enabling `alwaysOn` is a one-command fix. If on Free/Shared, a plan upgrade is required.
6. **46 unreleased commits:** Confirm whether the production deployment lag is intentional (release gating) or unintentional (forgotten redeploy).
