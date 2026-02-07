# Azure DEV Environment - App Settings Canon

**Last Updated:** 2026-02-07  
**Purpose:** Single source of truth for critical Azure App Service settings in DEV environment

## Critical Settings for CI/Smoke Tests

### CI Smoke Test Credentials
These enable the Azure DEV Smoke workflow to test deployed API:

```
CI_SMOKE_USERNAME = "ci@crown-demo.local"
CI_SMOKE_PASSWORD = "CrownCiSmoke!2026"  # ROTATE AFTER STABILIZATION
CI_SMOKE_SCHOOL_ID = "a5351136-98fe-4d48-add0-fa8f62d9ceff"
```

**Security Notes:**
- CI user should have minimal permissions (read-only + roster view)
- Password should be rotated quarterly (store in GitHub Secrets + Azure App Settings)
- School ID must match canonical seed script (seed_a535.py)

### OPS Secrets Alignment
OPS endpoints use header-based authentication:

```
CROWN_OPS_SECRET = "DevOpsSecret_Crown2026_Smoke_Testing_af94be6e9f6642c998ce_XyZ9QwErTyUiOp"
DEV_OPS_SECRET = "DevOpsSecret_Crown2026_Smoke_Testing_af94be6e9f6642c998ce_XyZ9QwErTyUiOp"
```

**Why Both?**
- `CROWN_OPS_SECRET`: Used by demo-reset endpoint
- `DEV_OPS_SECRET`: Used by ensure-ci-user endpoint
- **MUST MATCH** for workflow consistency
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

## Related Files

- `backend/core/seed_helpers.py` - Canonical deterministic school creation
- `backend/crown_api/ops_views.py` - ensure_ci_user endpoint
- `backend/core/management/commands/golden_path_bootstrap.py` - Bootstrap command
- `seed_a535.py` - Local seed script (shares same UUID)
