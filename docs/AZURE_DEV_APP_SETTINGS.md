# Azure DEV Environment - App Settings Canon

**Last Updated:** 2026-02-07
**Purpose:** Single source of truth for critical Azure App Service settings in DEV environment

## Critical Settings for CI/Smoke Tests

### CI Smoke Test Credentials
These enable the Azure DEV Smoke workflow to test deployed API:

```
CI_SMOKE_USERNAME = "ci@crown-demo.local"
CI_SMOKE_PASSWORD = "<REDACTED_SEE_AZURE_APP_SETTINGS>"
CI_SMOKE_SCHOOL_ID = "a5351136-98fe-4d48-add0-fa8f62d9ceff"
```

**Security Notes:**
- **NEVER commit real passwords to git.** Fetch from Azure App Settings or GitHub Secrets.
- CI user should have minimal permissions (read-only + roster view)
- Password should be rotated quarterly (store in GitHub Secrets + Azure App Settings)
- School ID must match canonical seed script (seed_a535.py)

### OPS Secrets Alignment
OPS endpoints use header-based authentication:

```
CROWN_OPS_SECRET = "<REDACTED_SEE_AZURE_APP_SETTINGS_OR_GITHUB_SECRETS>"
DEV_OPS_SECRET = "<REDACTED_SEE_AZURE_APP_SETTINGS_OR_GITHUB_SECRETS>"
```

**Why Both?**
- `CROWN_OPS_SECRET`: Used by demo-reset endpoint
- `DEV_OPS_SECRET`: Used by ensure-ci-user endpoint
- **MUST MATCH** for workflow consistency
- **ROTATE IMMEDIATELY if exposed in logs/chat/commits**
- Workflows reference GitHub Secret `DEV_OPS_SECRET`

### Build/Version Tracking
```
BUILD_SHA = <git-commit-sha>  # Set by CI/CD pipeline
ENVIRONMENT = "dev"
```

## How Settings Are Applied

### Via Azure CLI:
```bash
az webapp config appsettings set \
  -g crown-rg \
  -n crown-api-dev \
  --settings \
    CI_SMOKE_USERNAME="ci@crown-demo.local" \
    CI_SMOKE_PASSWORD="..." \
    CI_SMOKE_SCHOOL_ID="a5351136-98fe-4d48-add0-fa8f62d9ceff"

# Restart required for app to pick up changes
az webapp restart -g crown-rg -n crown-api-dev
```

### Via Azure Portal:
1. Navigate to: crown-api-dev → Settings → Environment variables
2. Add/Update Application Settings
3. Click "Save" (triggers automatic restart)

## Drift Prevention Rules

1. **Never hardcode these values in code** - always read from environment
2. **Document changes here immediately** - prevents tribal knowledge
3. **CI_SMOKE_SCHOOL_ID must match seed_a535.py** - enforced by `seed_helpers.ensure_deterministic_school()`
4. **Rotate secrets quarterly** - set calendar reminder

## Workflows Depending on These Settings

- `dev-smoke-azure-dev.yml` (Azure DEV Smoke)
- `ops-reset-dev.yml` (OPS Reset DEV Demo)

## Troubleshooting

**Symptom:** Azure DEV Smoke fails with "Server misconfigured: missing CI_SMOKE_*"
**Fix:** Verify all three CI_SMOKE_* settings are present via Azure CLI or Portal

**Symptom:** OPS reset returns "Forbidden"
**Fix:** Ensure CROWN_OPS_SECRET matches GitHub Secret DEV_OPS_SECRET

**Symptom:** "School not found" even after OPS reset
**Fix:** Verify CI_SMOKE_SCHOOL_ID matches the canonical UUID (a5351136...)

**Symptom:** Azure behaving weirdly / endpoints returning unexpected data
**Fix:** **ALWAYS CHECK BUILD_SHA FIRST** before debugging anything else:
```powershell
curl.exe -s https://crown-api-dev.azurewebsites.net/api/health/ | python -m json.tool
```
**Rule:** If `build_sha` != expected commit, stop debugging and fix deployment first. Stale code causes phantom bugs.

## BUILD_SHA: Stale Code Detection

**Current Mechanism:**
- `backend/crown_api/build_info.py` contains `BUILD_SHA = "local-dev"` (default)
- CI/CD pipeline overwrites this file during build with actual commit SHA
- `/api/health/` endpoint returns `build_sha` field
- Post-deploy workflows poll and **hard fail** if mismatch

**How to Check:**
```powershell
# Get current deployed version
curl.exe -s https://crown-api-dev.azurewebsites.net/api/health/ | python -m json.tool

# Compare with expected (latest main)
git log --oneline -1 main
```

**Drift Prevention:**
- **BEFORE** debugging Azure issues: verify BUILD_SHA matches expected commit
- **AFTER** merging PRs: wait for deployment, verify BUILD_SHA updated
- **IF** build_sha is stale: deployment pipeline failed, check GitHub Actions

**Workflows with Hard Fail:**
- `stabilization-20260116-spine_crown-api-dev.yml` (DEV deploy): Polls 32 times, exits 1 if mismatch
- `deploy-prod.yml` (PROD deploy): Polls 30 times, exits 1 if mismatch
- `dev-smoke-azure-dev.yml` (Smoke test): Uses `jq -e` to verify field exists

## Related Files

- `backend/core/seed_helpers.py` - Canonical deterministic school creation
- `backend/crown_api/ops_views.py` - ensure_ci_user endpoint
- `backend/core/management/commands/golden_path_bootstrap.py` - Bootstrap command
- `seed_a535.py` - Local seed script (shares same UUID)
- **`backend/crown_api/build_info.py`** - BUILD_SHA variable (overwritten by CI)
- **`backend/crown_api/version_views.py`** - /api/health/ endpoint implementation
- **`.github/workflows/stabilization-20260116-spine_crown-api-dev.yml`** - DEV deployment + BUILD_SHA verification
- **`.github/workflows/deploy-prod.yml`** - PROD deployment + BUILD_SHA verification


## Reviewed inquiry migration prerequisite (2026-10-19)

The existing `deploy-dev.yml` workflow verifies that the selected full source SHA is an ancestor of freshly fetched accepted `main` before loading checked-out dependencies or Azure configuration. This check does not automatically select the latest `main`; the operator selects the intended full SHA and ties the evidence to it. The existing DEV runner and federation execute `scripts/ops/run_dev_inquiry_migration.py` before any application-setting or image mutation. The `rc/**` and manual triggers are unchanged; no separate service or startup migration flag is introduced.

The helper reads only `crown-rg/crown-api-dev` and its existing Key Vault references. It requires the current DEV environment markers, the exact `crown-pg-dev.postgres.database.azure.com` PostgreSQL host and port, an explicit non-system database from that app's configuration, matching effective/connected database identity, the public schema, a primary connection, and hostname-verified TLS. Credentials stay in the runner process and are excluded from evidence.

The reviewed change is only `crm_marketing.0002_inquiry_capture`; its SHA-256 is `b4224adf8e10c05e836a164200ff6c0552067491006c8dc2fc3a3095cc7743eb`, pinned in the helper. Planning, identity verification, the existing `migrate_with_lock` command, and the final currency check share the existing PostgreSQL advisory lock. An empty plan performs checks only. Any other pending migration, missing predecessor, reverse plan, modified migration file, target mismatch, or unavailable access stops the job before deployment. DDL authority must already exist; the helper creates no role, secret, network rule, or Azure resource and sends no messages.

The migration keeps database defaults for its 14 new non-null `MarketingLead` fields. The historical-model regression uses the actual `0001_initial` model to insert without those columns, then reads the row through the current model. Before the first DEV application of this migration, the owner/operator must retain a passing [isolated PostgreSQL drill](operations/ISOLATED_POSTGRES_RESTORE_DRILL.md) for the selected source: its evidence packet requires both restore success and this one unskipped regression with normal migrations on PostgreSQL 16. The drill uses a generated source database and a separate disposable pytest database. It does not use a live DEV or production database.

The final deployment JSON evidence records source SHA, DEV app, verified database-identity fingerprint, applied migration names and zero remaining migrations, or a sanitized BLOCKED reason. Rejected pending plans include up to 20 validated migration identifiers and directions, the total count and a truncation flag, with source SHA and DEV app context; they never include SQL or raw provider errors. A green unit test proves these controls, not hosted DDL privileges or network availability. Actual DEV connection, permissions, migration execution and subsequent health/SHA checks must succeed before this deployment is reported as complete.

If blocked, retain the current API image and inspect the sanitized failure stage. Do not toggle the obsolete `RUN_MIGRATE` setting, weaken startup `migrate --check`, use the production migration workflow for DEV, or widen the permitted plan. Unexpected migration or permission requirements need their own reviewed disposition. If schema application succeeds and a later image deployment fails, preserve the additive schema and captured data. The persistent defaults and historical-model test establish the legacy `MarketingLead` INSERT/read boundary only; they do not certify every previous-image endpoint against new inquiry data or complete an Azure rollback. The operator must verify the chosen rollback image against the retained schema before relying on it. A later deployment failure does not authorize reversing the migration and deleting captured data.

Local boundary proof (no database or Azure execution): `python -m unittest discover -s scripts/ops -p test_run_dev_inquiry_migration.py -v`.
