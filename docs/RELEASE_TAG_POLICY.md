# Release Tag Policy

## Immutability Rule

**All `crown-*` release tags are immutable once pushed to origin.**

- Tags represent specific points in history for auditing, compliance, and investor demos
- Moving a tag rewrites history and breaks SHA-based verification
- If a follow-on fix is needed, create a new tag (e.g., `crown-0.3.1-*`), don't rewrite `crown-0.3.0-*`

## Tag Naming Convention

### Spine/Feature Tags
- `crown-X.Y.Z-<descriptor>`
- Examples:
  - `crown-0.3.0-spine-complete` - Baseline with tenant isolation + CI
  - `crown-0.3.1-prod-pipeline-aligned` - Prod workflow aligned with DEV

### Hotfix Tags
- `crown-X.Y.Z-hotfix-<issue>`
- Examples:
  - `crown-0.3.2-hotfix-auth`

## Tag Creation Workflow

1. **Create tag locally**:
   ```powershell
   git tag crown-X.Y.Z-descriptor <commit-sha> -m "Description"
   ```

2. **Push to origin** (one-time only):
   ```powershell
   git push origin crown-X.Y.Z-descriptor
   ```

3. **Never force-push** or delete/recreate tags on origin

## Deployment Verification

All deployments must verify against immutable tags:

```powershell
# Local
$expected = git rev-parse --short=7 crown-X.Y.Z-descriptor

# DEV
$dev = curl.exe -s https://crown-api-dev.azurewebsites.net/api/health/ | ConvertFrom-Json
$dev.build_sha -eq $expected

# PROD
$prod = curl.exe -s https://crown-api-prod.azurewebsites.net/api/health/ | ConvertFrom-Json
$prod.build_sha -eq $expected
```

## Current Spine Tags

| Tag | Commit | Description |
|-----|--------|-------------|
| `crown-0.3.0-spine-complete` | `6a86f74` | Tenant isolation canon + CI + health SHA verification |
| `crown-0.3.1-prod-pipeline-aligned` | `8241bfe` | Prod workflow fixed to bake SHA into artifact |

## Enforcement

- **Manual**: Code review must reject PRs that attempt to move existing `crown-*` tags
- **Automated** (optional): CI job validates spine tags against `docs/SPINE_TAGS.json`

## Rationale

Immutable tags enable:
- **Audit trail**: "This exact code was demoed to investor X on date Y"
- **SHA verification**: `/api/health/` proves deployed code matches tag
- **Rollback confidence**: Revert to known-good commit without ambiguity
- **CI reproducibility**: Workflows can checkout tags and get identical builds
