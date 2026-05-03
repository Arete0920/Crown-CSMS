# Crown 2026 — Environment Links Reference
**Generated:** 2026-05-01  
**Status:** Production CERTIFIED (automated gate PASS, 2026-05-01T13:15:37)  
**Scope:** One-click links for post-certification manual lane execution  

---

## PRODUCTION

| Resource | URL | Status |
|---|---|---|
| **Frontend App** | https://yellow-forest-0eecc8b0f.7.azurestaticapps.net | ✅ HTTP 200 |
| **Backend Health** | https://crown-api-prod.azurewebsites.net/api/health/ | ✅ HTTP 200 |
| **Build Metadata** | https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/build.json | ✅ HTTP 200 |
| **Backend API Root** | https://crown-api-prod.azurewebsites.net/api/v1/ | — |
| **Portal: crown-api-prod** | https://portal.azure.com/#@/resource/subscriptions/4ef0ba4b-4810-48d4-b3fe-953a9708953a/resourceGroups/crown-rg/providers/Microsoft.Web/sites/crown-api-prod/overview | — |
| **Portal: crown-dash (SWA)** | https://portal.azure.com/#@/resource/subscriptions/4ef0ba4b-4810-48d4-b3fe-953a9708953a/resourceGroups/crown-rg/providers/Microsoft.Web/staticSites/crown-dash/overview | — |
| **Portal: Resource Group** | https://portal.azure.com/#@/resource/subscriptions/4ef0ba4b-4810-48d4-b3fe-953a9708953a/resourceGroups/crown-rg/overview | — |

**Prod build stamp (verified 2026-05-01):**
- Backend SHA: `c7ab4328516ad0354d20606c5e6a60d05dc07b73`
- Frontend SHA: `84b780b97001c1fb4f7ce8f3b2f099e99835ae4f`
- Deploy tag: `prod-deploy-20260501-rc3`

---

## SANDBOX / DEV

| Resource | URL | Status |
|---|---|---|
| **Backend Health** | https://crown-api-dev.azurewebsites.net/health/ | ✅ HTTP 200 |
| **Backend API Root** | https://crown-api-dev.azurewebsites.net/api/v1/ | — |
| **Local Frontend** | http://localhost:3000 | run `npm run dev` |
| **Local Backend** | http://localhost:8000 | run `python manage.py runserver` |
| **Portal: crown-api-dev** | https://portal.azure.com/#@/resource/subscriptions/4ef0ba4b-4810-48d4-b3fe-953a9708953a/resourceGroups/crown-rg/providers/Microsoft.Web/sites/crown-api-dev/overview | — |

**Sandbox build stamp (verified 2026-05-01):**
- Build SHA: `dev-pass4fix-20260329150550-bg`
- Version: `crown-0.3.0`
- DB: `ok`
- Deploy workflow: `live-rollback-drill`
- Demo mode: `false`

> **Note:** No persistent sandbox frontend SWA is deployed. The `crown-api-dev` App Service is the only live sandbox service. Frontend testing runs locally or via the prod SWA against the dev API base.

---

## AZURE SUBSCRIPTION

| Resource | Value |
|---|---|
| Subscription Name | CROWN Christian School Management |
| Subscription ID | `4ef0ba4b-4810-48d4-b3fe-953a9708953a` |
| Resource Group | `crown-rg` (eastus) |
| Container Registry | `crownregistry.azurecr.io` |
| Portal: Subscription | https://portal.azure.com/#@/resource/subscriptions/4ef0ba4b-4810-48d4-b3fe-953a9708953a/overview |
| Portal: All Resources | https://portal.azure.com/#blade/HubsExtension/BrowseAll |

---

## GITHUB ACTIONS (Key Workflows)

| Workflow | Purpose | Link |
|---|---|---|
| `deploy-prod.yml` | Backend prod deploy (triggered on `prod-deploy-*` tags) | https://github.com/tcmegahan/Crown2026/actions/workflows/deploy-prod.yml |
| `deploy-dashboard.yml` | Frontend prod deploy (triggered on `prod-deploy-*` tags) | https://github.com/tcmegahan/Crown2026/actions/workflows/deploy-dashboard.yml |
| `deploy-dev.yml` | Dev/sandbox backend deploy (triggered on `rc/**` pushes) | https://github.com/tcmegahan/Crown2026/actions/workflows/deploy-dev.yml |
| `prod-integrity-proof.yml` | Post-deploy SHA proof ceremony | https://github.com/tcmegahan/Crown2026/actions/workflows/prod-integrity-proof.yml |
| `ci.yml` | Main CI gate | https://github.com/tcmegahan/Crown2026/actions/workflows/ci.yml |
| **All Actions** | — | https://github.com/tcmegahan/Crown2026/actions |

---

## QUICK COPY BLOCK (paste into Slack/Teams)

```
Crown 2026 Environment Links — 2026-05-01

PRODUCTION
  App:           https://yellow-forest-0eecc8b0f.7.azurestaticapps.net
  API Health:    https://crown-api-prod.azurewebsites.net/api/health/
  Build JSON:    https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/build.json
  Azure Portal:  https://portal.azure.com/#@/resource/subscriptions/4ef0ba4b-4810-48d4-b3fe-953a9708953a/resourceGroups/crown-rg/overview

SANDBOX/DEV
  API Health:    https://crown-api-dev.azurewebsites.net/health/
  Local App:     http://localhost:3000  (npm run dev)
  Local API:     http://localhost:8000

GITHUB
  Actions:       https://github.com/tcmegahan/Crown2026/actions
  Repo:          https://github.com/tcmegahan/Crown2026
```

---

## RELATED OPERATIONAL DOCS

| Doc | Purpose |
|---|---|
| [POST_CERT_LAUNCH_PLAYBOOK_20260501.md](POST_CERT_LAUNCH_PLAYBOOK_20260501.md) | T-0 kickoff sequence, milestones, escalation rules |
| [POST_CERT_DEV_RUNTIME_PROOF_CHECKLIST_20260501.md](POST_CERT_DEV_RUNTIME_PROOF_CHECKLIST_20260501.md) | 26 manual proof rows, dev owner assignments |
| [POST_CERT_TENANT_RISK_TRIAGE_WORKSHEET_20260501.md](POST_CERT_TENANT_RISK_TRIAGE_WORKSHEET_20260501.md) | 212 static risk hit triage guide |
| [POST_CERT_FOUNDER_PRODUCT_OWNER_HANDOFF_20260501.md](POST_CERT_FOUNDER_PRODUCT_OWNER_HANDOFF_20260501.md) | Executive summary, open items, escalation policy |
