# GitHub Actions Version Audit

**Date**: January 27, 2026  
**Status**: 3 deprecations found in deploy-prod.yml

---

## Summary

| Workflow | Status | Issues |
|----------|--------|--------|
| ci.yml | ✅ Current | None |
| msgraph-smoke.yml | ✅ Current | None |
| stabilization-20260116-spine_crown-api-dev.yml | ✅ Current | None |
| deploy-prod.yml | ⚠️ Outdated | 3 actions need updates |

---

## Detailed Findings

### ✅ ci.yml (Current)
```yaml
actions/checkout@v4           # Latest stable
actions/setup-python@v5       # Latest stable
```

### ✅ msgraph-smoke.yml (Current)
```yaml
actions/checkout@v4           # Latest stable
azure/login@v2                # Latest stable
```

### ✅ stabilization-20260116-spine_crown-api-dev.yml (Current)
```yaml
actions/checkout@v4           # Latest stable
actions/setup-python@v5       # Latest stable
azure/login@v2                # Latest stable
azure/webapps-deploy@v3       # Latest stable
```

### ⚠️ deploy-prod.yml (Needs Updates)

**Outdated Actions**:

1. **actions/setup-python@v4** → Should be **v5**
   - Status: v4 still supported but v5 is current
   - Impact: Low (v4 works fine, v5 adds minor improvements)
   - Priority: Medium

2. **azure/login@v1** → Should be **v2**
   - Status: v1 deprecated, v2 is current
   - Impact: Medium (v1 may stop working in future Azure updates)
   - Priority: **High**

3. **azure/webapps-deploy@v2** → Should be **v3**
   - Status: v2 functional but v3 is current
   - Impact: Medium (v3 adds better deployment verification)
   - Priority: **High**

**Other Actions in deploy-prod.yml** (Current):
```yaml
actions/checkout@v4           # ✅ Latest
docker/setup-buildx-action@v3 # ✅ Latest
docker/build-push-action@v5   # ✅ Latest
aquasecurity/trivy-action@master  # ⚠️ Should pin to version tag
github/codeql-action/upload-sarif@v3  # ✅ Latest
codecov/codecov-action@v3     # ✅ Latest
slackapi/slack-github-action@v1.24.0  # ✅ Pinned version
```

---

## Recommended Updates

### Priority 1: Fix deploy-prod.yml

```yaml
# Before
- uses: actions/setup-python@v4
- uses: azure/login@v1
- uses: azure/webapps-deploy@v2

# After
- uses: actions/setup-python@v5
- uses: azure/login@v2
- uses: azure/webapps-deploy@v3
```

### Priority 2: Pin trivy-action version

```yaml
# Before
- uses: aquasecurity/trivy-action@master  # Unstable, tracks HEAD

# After
- uses: aquasecurity/trivy-action@0.30.0  # Pin to stable release
```

---

## Deprecation Risk Assessment

| Action | Current Version | Latest Version | Deprecation Risk | Breaking Soon? |
|--------|----------------|----------------|------------------|----------------|
| actions/checkout@v4 | v4 | v4 | None | No |
| actions/setup-python@v4 | v4 | v5 | Low | No (v4 maintained) |
| actions/setup-python@v5 | v5 | v5 | None | No |
| azure/login@v1 | v1 | v2 | **High** | **Possibly** |
| azure/login@v2 | v2 | v2 | None | No |
| azure/webapps-deploy@v2 | v2 | v3 | Medium | No (v2 maintained) |
| azure/webapps-deploy@v3 | v3 | v3 | None | No |
| docker/setup-buildx-action@v3 | v3 | v3 | None | No |
| docker/build-push-action@v5 | v5 | v5 | None | No |
| aquasecurity/trivy-action@master | master | 0.30.0 | **High** | **Yes** (unstable) |
| github/codeql-action/upload-sarif@v3 | v3 | v3 | None | No |
| codecov/codecov-action@v3 | v3 | v4 | Low | No (v3 maintained) |
| slackapi/slack-github-action@v1.24.0 | v1.24.0 | v2.x | Low | No (v1 maintained) |

---

## Implementation Plan

### Phase 1: Critical (Do Now)
- Update deploy-prod.yml: azure/login@v1 → v2
- Update deploy-prod.yml: azure/webapps-deploy@v2 → v3
- Pin trivy-action to stable version

### Phase 2: Recommended (Next Sprint)
- Update deploy-prod.yml: actions/setup-python@v4 → v5
- Consider: codecov-action@v3 → v4
- Consider: slack-github-action@v1.24.0 → v2.x

### Phase 3: Monitoring (Quarterly Review)
- Check for new major versions
- Review GitHub Actions changelog
- Audit Docker base images (python:3.12-slim)

---

## Other Infrastructure Versions

**Python**: 3.12 (current, stable)  
**Django**: 5.2.8 (current LTS-track)  
**Docker Base**: python:3.12-slim (current)  
**Azure App Service Runtime**: Python 3.12 Linux (current)

No immediate concerns with infrastructure versions.

---

## Next Steps

1. Create PR to update deploy-prod.yml with critical updates
2. Test deployment to DEV first
3. Deploy to PROD after verification
4. Schedule quarterly version audit (April 2026)
