# CROWN PR — Active Lane Required

## Active Lane

- PR:
- Branch:
- Worktree:
- Base SHA:
- Head SHA:
- Goal:
- Evidence output path:
- Completion claim allowed: no
- Independent review required: yes

## Purpose (1 sentence)

<!-- What does this PR do? -->

## Scope / Blast Radius (must be explicit)

**Allowed changed files / directories (exact list):**
-

**Forbidden files / directories:**
- Everything else

## Lane Guard

- [ ] Active lane packet exists
- [ ] `scripts/guards/assert_active_lane.ps1 -Lane <path>` ran and passed
- [ ] Worktree was clean before validation
- [ ] Final `git status --short` captured
- [ ] Changed files match allowed scope

## Proof Policy Gate

**If this PR touches any of these, Proof — Gradebook must run + pass:**
- `.github/workflows/proof-gradebook.yml`
- `frontend/dashboards/tests/**`
- `frontend/dashboards/src/**`
- `backend/gradebook/**`
- `backend/academics/**`
- `backend/core/management/commands/**`
- `backend/crown_api/**`

- [ ] Proof — Gradebook (UI + API) ran and passed, if required
  - Proof run link:

## Dashboard Certification Safety

- [ ] This PR does not claim dashboard certification unless the matrix row is independently reviewed and promoted to CERTIFIED.
- [ ] This PR does not use sample data as production proof.
- [ ] This PR does not ask TC to self-review or self-approve.

## Proof (required)

Paste raw outputs or artifact paths.

### Local

```bash
git status -sb
git diff --stat
python backend/manage.py check
```

### CI / Validation

- pytest:
- frontend unit tests:
- frontend build:
- Spine Audit (Canon Guard):
- Proof Ceremony:
- Secret Scan:
- CI - Tests and Checks:

### Deploy Determinism (if deploy-related)

- /health/ returns {"build_sha":"<sha>"} (not local-dev)
- Workflow log contains: OK build_sha:

## Remaining NOT DONE / NOT VERIFIED

-

## Rollback plan (1 line)

<!-- example: revert commit / revert PR -->
