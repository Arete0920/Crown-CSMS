# Spine PR  No Wandering

## Purpose (1 sentence)
<!-- What does this PR do? -->

## Scope / Blast Radius (must be explicit)
**Allowed changed files / directories (exact list):**
- 

**Forbidden (anything not listed above):**
- Everything else

## Proof Policy Gate
**If this PR touches any of these, Proof — Gradebook must run + pass:**
- `.github/workflows/proof-gradebook.yml`
- `frontend/dashboards/tests/**`
- `frontend/dashboards/src/**`
- `backend/gradebook/**`
- `backend/academics/**`
- `backend/core/management/commands/**`
- `backend/crown_api/**`

- [ ] Proof — Gradebook (UI + API) ran and passed (auto-runs on relevant changes)
  - Proof run link: (if manual trigger used)

## Proof (required)
Paste raw outputs (no interpretation):

### Local
```bash
git status -sb
git diff --stat
python backend/manage.py check
```

### CI (PR checks)
- pytest: 
- Spine Audit (Canon Guard): 
- Proof Ceremony: 
- Secret Scan: 
- CI - Tests and Checks: 

### Deploy Determinism (if deploy-related)
- /health/ returns {"build_sha":"<sha>"} (not local-dev)
- Workflow log contains: OK build_sha:

## Rollback plan (1 line)
<!-- example: revert commit / revert PR -->

