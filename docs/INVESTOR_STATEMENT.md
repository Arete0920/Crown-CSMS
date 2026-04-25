# Investor-Ready Production Statement

**Date**: January 27, 2026
**Status**: ✅ Production Verified

---

## Deployed Code

**Production is running commit `8241bfe`** (crown-0.3.1-prod-pipeline-fix)

- **DEV**: `https://crown-api-dev.azurewebsites.net` → `8241bfe`
- **PROD**: `https://crown-api-prod.azurewebsites.net` → `8241bfe`

### Verification
```powershell
curl https://crown-api-dev.azurewebsites.net/api/health/
# {"ok": true, "status": "ok", "build_sha": "8241bfe"}

curl https://crown-api-prod.azurewebsites.net/api/health/
# {"ok": true, "status": "ok", "build_sha": "8241bfe"}
```

---

## Release Lineage

```
6a86f74 (crown-0.3.0-spine-complete)
   │
   │  Tenant isolation canon + CI + SHA verification
   │  - 8/8 tenant isolation tests passing
   │  - Migration checks prevent schema drift
   │  - DEV workflow bakes SHA into artifact
   │
   └─→ 8241bfe (crown-0.3.1-prod-pipeline-fix) [DEPLOYED]

      Pipeline parity: PROD workflow aligned with DEV
      - Bakes SHA into artifact (no appsettings mutation)
      - Eliminates SCM container restart conflict
      - Both environments use identical deployment pattern
```

### Why Two Tags?

The **spine release** (0.3.0 at `6a86f74`) completed the foundational tenant isolation work. However, the PROD deployment workflow still used the old appsettings method while DEV had already been updated to bake the SHA.

**Pipeline parity required one additional commit** (`8241bfe`) to align PROD with DEV. This is what's deployed.

Per release discipline policy: tags are immutable. We don't move `crown-0.3.0-spine-complete` to point at `8241bfe` - we create a new tag `crown-0.3.1-prod-pipeline-fix`.

---

## What's in Production

### Core Capabilities
1. **Multi-tenant isolation**: Every API enforces school_id scoping
2. **SHA verification**: `/api/health/` proves deployed code matches commit
3. **CI discipline**: Tests + migrations checked on every PR/merge
4. **Pipeline parity**: DEV and PROD use identical deployment patterns

### Test Coverage
- 8/8 tenant isolation tests passing
- Cross-tenant queries return 404 (not 403)
- Missing tenant context returns 400
- Staff can override via `X-School-Id` header

### Documentation
- [TENANT_PRIVACY_CANON.md](../docs/TENANT_PRIVACY_CANON.md) - Constitutional rules for tenant isolation
- [RELEASE_TAG_POLICY.md](../docs/RELEASE_TAG_POLICY.md) - Tag immutability enforcement
- [RELEASE_NOTES.md](../docs/RELEASE_NOTES.md) - Complete release history

---

## CI Protections

The following checks run on every PR and merge to main:

1. **Tag immutability**: CI fails if `crown-0.3.0-spine-complete` has moved from `6a86f74`
2. **Migration check**: `makemigrations --check` prevents schema drift
3. **Test suite**: Core API tests must pass
4. **Health endpoint**: Local health check validates deployability

See [.github/workflows/ci.yml](../.github/workflows/ci.yml) for implementation.

---

## Deployment Verification Commands

```powershell
# Verify tag hasn't moved
git fetch --tags
git rev-parse --short=7 crown-0.3.0-spine-complete  # Should be: 6a86f74

# Verify deployed code
$dev = curl.exe -s https://crown-api-dev.azurewebsites.net/api/health/ | ConvertFrom-Json
$prod = curl.exe -s https://crown-api-prod.azurewebsites.net/api/health/ | ConvertFrom-Json

Write-Host "DEV:  $($dev.build_sha)"   # Should be: 8241bfe
Write-Host "PROD: $($prod.build_sha)"  # Should be: 8241bfe
```

---

## Investor Summary

> "Crown API is deployed to Azure App Service in DEV and PROD environments. Production is running commit `8241bfe` (crown-0.3.1-prod-pipeline-fix), which includes the spine foundation (tenant isolation, CI discipline, SHA verification) plus pipeline parity improvements. The spine milestone tag (crown-0.3.0-spine-complete) points immutably to `6a86f74`. Both environments are verified operational with matching deployment SHAs. CI protections prevent tag movement and regression."

---

## Next Steps

With production validated at `8241bfe`:
1. ✅ Spine complete (tenant isolation + CI)
2. ✅ Pipeline parity achieved
3. ⏳ Actions version updates (deploy-prod.yml: python@v4→v5, azure/login@v1→v2, webapps-deploy@v2→v3)
4. ⏳ Day 2 endpoints (admissions funnel, finance summary, attendance)

Foundation is stable. Ready for incremental feature additions.
