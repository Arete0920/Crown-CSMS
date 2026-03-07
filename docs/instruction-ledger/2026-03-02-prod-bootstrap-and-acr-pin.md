# Prod Bootstrap, ACR Pin, and Credential Rotation
**Date:** 2026-03-02  
**Branch:** `fix/system-wiring-and-test-fixes` (PR #502)  
**HEAD at close:** `4807c9916edcfc7522578a5d5a98f450e44cb398`  
**Author:** ops session (GitHub Copilot / Claude Sonnet 4.6)

---

## A. Intent

1. Rotate leaked Postgres `crownapp` password (exposed in chat history — treat prior value as compromised)
2. Rotate Django admin password (exposed in chat history — treat prior value as compromised)
3. Ensure admin bootstrap is idempotent on container restart
4. Pin container image tag for demo stability (avoid `latest` drift)
5. Verify health endpoint + JWT auth path
6. Fix `env: "dev"` appearing in health response despite `ENVIRONMENT=prod` being set

---

## B. Commands Executed (sanitized — all secrets replaced with `<<<REDACTED>>>`)

### Postgres password rotation
```bash
az postgres flexible-server update \
  -g crown-rg \
  -n crown-db-prod \
  --admin-password <<<REDACTED>>>
```

### App Service settings update
```bash
az webapp config appsettings set -g crown-rg -n crown2026web --settings \
  "DATABASE_URL=postgres://crownapp:<<<REDACTED>>>@crown-db-prod.postgres.database.azure.com:5432/crown_db?sslmode=require" \
  "DB_PASSWORD=<<<REDACTED>>>" \
  "DJANGO_SUPERUSER_PASSWORD=<<<REDACTED>>>" \
  "CROWN_ENV=prod" \
  "BUILD_SHA=4807c9916edcfc7522578a5d5a98f450e44cb398"
```

### Login template fix (committed separately — no secrets)
```bash
# Remove hardcoded value="admin" from password field in login.html
# Commit: d791ea6d — "fix: remove hardcoded admin password from login template"
```

### ACR image build and pin
```bash
az acr build -g crown-rg -r crownregistry \
  --image crown2026:20260302b \
  --image crown2026:latest \
  .

az webapp config container set \
  -g crown-rg -n crown2026web \
  --container-image-name crownregistry.azurecr.io/crown2026:20260302b
```

### App Service restart
```bash
az webapp restart -g crown-rg -n crown2026web
```

---

## C. Result Proofs

| Signal | Result |
|--------|--------|
| ACR tags present | `20260302b`, `20260302`, `latest` confirmed via `az acr repository show-tags` |
| App Service image (`linuxFxVersion`) | `DOCKER\|crownregistry.azurecr.io/crown2026:20260302b` |
| `GET /api/health/` | HTTP 200, `"db": "ok"`, `"ok": true` |
| `POST /api/auth/token/` | Returns `access` + `refresh` tokens (do not store token values) |
| `entrypoint.sh` admin bootstrap | Idempotent `get_or_create + set_password` — handles re-runs without error |
| `CROWN_ENV=prod` set in App Service | Health endpoint will report `"env": "prod"` after next restart |
| `local.secrets.ps1` gitignored | Confirmed — not tracked by git |

---

## D. Known Anomaly at Time of Event

### `"env": "dev"` in health response while `ENVIRONMENT=prod` was set

**Root cause (confirmed by code inspection):**  
[`backend/crown_api/health_views.py` line 26](../../backend/crown_api/health_views.py#L26):
```python
env_name = os.getenv("CROWN_ENV", "dev")
```
The health view reads **`CROWN_ENV`** (not `ENVIRONMENT`).  
App Service had `ENVIRONMENT=prod` but **no `CROWN_ENV`** set → fell through to default `"dev"`.

**Fix applied this session:**  
`CROWN_ENV=prod` added to App Service settings (see section B above).  
No code change required — config-only fix.

**Related settings.py function** (uses a different set of env vars, consistent with itself):  
[`backend/crown_api/settings.py` line 289–296](../../backend/crown_api/settings.py#L289):
```python
def _env_is_prod() -> bool:
    v = (
        os.getenv("CROWN_ENV")
        or os.getenv("DJANGO_ENV")
        or os.getenv("ENVIRONMENT")
        or os.getenv("APP_ENV")
        or ""
    ).strip().lower()
    return v in {"prod", "production", "live"}
```
`_env_is_prod()` checks `CROWN_ENV` first — so this was also affected before the fix.

---

## E. Follow-up Risk Items

### 1. Least-privilege DB role gap (known exception — not fixed this session)
- Current state: `crownapp` is the **Postgres Flexible Server admin account** (server-level role)
- Risk: app connects as admin → any SQL injection or ORM bug has server-wide blast radius
- Recommended (not MVP-blocking): create a separate `crown_app_user` role with schema-limited  
  `CONNECT`, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on `crown_db` only; migrate `DATABASE_URL` to that user
- Migrations (which need DDL rights) should run as admin; app runtime should not

### 2. `BUILD_SHA` was `"local-dev"` in health response
- Image was built via `az acr build` which does not bake `GITHUB_SHA` into the image
- Fix applied: `BUILD_SHA` set explicitly in App Service settings to current HEAD SHA
- Long-term fix: CI/CD pipeline should pass `--build-arg BUILD_SHA=$GITHUB_SHA` to `az acr build`  
  and `ENV BUILD_SHA` in Dockerfile

### 3. Hardcoded insecure `SECRET_KEY` fallback in settings.py
- [`settings.py` line 50](../../backend/crown_api/settings.py#L50) has a hardcoded fallback:  
  `"django-insecure-77tws%k1#a!#aio14%6=4z6wn@_nrnu1d$(bur5-!2$-8+l$d2"`
- On Azure, `DJANGO_SECRET_KEY` is set as an App Service setting → fallback should not be reached
- Verify: `az webapp config appsettings list --query "[?name=='DJANGO_SECRET_KEY']"`

### 4. `gradebook.0001_initial` migration cold-start risk
- Historical: this migration took ~25s on 2026-03-01, causing container SIGTERM during health-check window
- Current gunicorn timeout: 60s — may not be sufficient if Postgres is cold
- Mitigation option: increase App Service startup health-check delay or raise gunicorn `--timeout 120`

---

## F. Credential Protocol (permanent rule — applies to all future sessions)

| Rule | Details |
|------|---------|
| Never paste live credentials in chat | Use `<<<ADMIN_PASS>>>`, `<<<DB_PASS>>>` as placeholders |
| Source of truth for secrets | Azure App Service settings (read via `az webapp config appsettings list`) |
| Local dev secrets | `local.secrets.ps1` (gitignored) — sourced with `. .\local.secrets.ps1` |
| JWT tokens | Never store or log token bodies — confirm auth by checking HTTP status only |
| After any rotation | Immediately verify `az webapp restart` + health check returns 200 |
