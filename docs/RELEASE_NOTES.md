# Release Notes

## crown-0.3.1-prod-pipeline-fix (2026-01-27)
**Commit**: `8241bfe`  
**Status**: Deployed to DEV and PROD

### Changes
- **Prod workflow alignment**: Updated `.github/workflows/deploy-prod.yml` to bake `BUILD_SHA` into artifact (`backend/crown_api/build_info.py`) instead of mutating Azure App Settings
- **Deployment parity**: PROD now uses identical SHA-baking pattern as DEV workflow
- **Issue fixed**: Eliminated SCM container restart conflict caused by appsettings mutation during deployment

### Why This Matters
The spine release (0.3.0) included the DEV workflow fix but PROD workflow still used the old appsettings method. This commit achieves full pipeline parity - both environments now use the same deployment pattern.

### Deployment Verification

**Prod must match `crown-0.3.1-prod-pipeline-fix`, verified via `/api/health/`**

```powershell
# Automated verification
$expected = git rev-parse --short=7 crown-0.3.1-prod-pipeline-fix
$prod = (curl.exe -s https://crown-api-prod.azurewebsites.net/api/health/ | ConvertFrom-Json).build_sha
if ($prod -ne $expected) { throw "Prod mismatch: expected $expected got $prod" }
Write-Host "✅ PROD verified at $expected" -ForegroundColor Green

# Manual check
curl https://crown-api-dev.azurewebsites.net/api/health/  # build_sha: 8241bfe
curl https://crown-api-prod.azurewebsites.net/api/health/ # build_sha: 8241bfe
```

### App Service Configuration Requirements

**Required environment variables for each environment:**

- **PROD** App Service must include: `CROWN_ENV=prod`
- **DEV** App Service should include: `CROWN_ENV=dev`

These settings control DRF renderer policy:
- PROD: JSON-only (no browsable API HTML)
- DEV: JSON + Browsable API (developer ergonomics)

---

## crown-0.3.0-spine-complete (2026-01-27)
**Commit**: `6a86f74`  
**Status**: Reference milestone (not deployed)

### Changes
- **Tenant isolation canon**: Created `docs/TENANT_PRIVACY_CANON.md` defining mandatory tenant context rules
- **Tenant isolation framework**: 
  - `MissingSchoolContext` exception (400 error for missing tenant)
  - `get_request_school_id(required=True)` helper in `backend/households/scoping.py`
  - Cross-tenant queries return 404 (not 403) to prevent tenant enumeration
- **Test coverage**: 8/8 tenant isolation tests passing (`backend/households/tests/test_tenant_isolation.py`)
- **CI discipline**: 
  - Created `.github/workflows/ci.yml` with fail-fast checks for migrations, tests, and health endpoint
  - Migration checks prevent silent schema drift
  - Test failures block PR merges
- **SHA verification**: 
  - `backend/crown_api/build_info.py` stores deployment SHA as artifact-level constant
  - `backend/crown_api/health_views.py` exposes SHA via `/api/health/` endpoint
  - DEV workflow updated to bake SHA (PROD workflow updated in 0.3.1)

### Why This Matters
This release establishes the **spine** - the minimal, stable foundation for multi-tenant operations:
- Every request must have tenant context (no global queries)
- Staff can override via `X-School-Id` header
- Tests prove tenant isolation works
- CI prevents regressions
- Deployments are verifiable via SHA

### Known Limitations
- PROD workflow still uses old appsettings method (fixed in 0.3.1)
- Actions versions outdated in deploy-prod.yml (fixed in 0.3.1)

---

## Release Lineage

```
6a86f74 (crown-0.3.0-spine-complete) - Tenant isolation + CI foundation
   │
   └─→ 8241bfe (crown-0.3.1-prod-pipeline-fix) - PROD workflow parity [DEPLOYED]
```

## Deployment Status

| Environment | Commit | Tag |
|-------------|--------|-----|
| DEV | `8241bfe` | crown-0.3.1-prod-pipeline-fix |
| PROD | `8241bfe` | crown-0.3.1-prod-pipeline-fix |

## Tag Policy

All `crown-*` tags are **immutable**. See [RELEASE_TAG_POLICY.md](RELEASE_TAG_POLICY.md) for details.

If a follow-on fix is needed:
- ❌ Don't move existing tag
- ✅ Create new tag (e.g., `crown-0.3.2-*`)
