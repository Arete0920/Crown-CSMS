# Production Deploy / Rollback / Restore Proof — 2026-02-23

## Pipeline integrity proof

| Event | Tag | SHA | Run ID | Verify Step |
|-------|-----|-----|--------|-------------|
| Deploy proof | `prod-deploy-2026-02-23-1816` | `25f3b9d4` | `22329017590` | ✅ success |
| Rollback drill | `prod-deploy-rollback-20260223-1827` | `2d91b96a` | `22329344476` | ✅ success |
| Prod restore | `prod-deploy-2026-02-23-1845` | `25f3b9d4` | `22329859358` | ✅ success |

Rollback tag deleted (local + remote).

## What was proven

- Tag-driven deploy is deterministic: push `prod-deploy-*` tag → workflow fires → correct image built and deployed.
- `/health` SHA verification works: step [27] matched `build_sha` to the pushed tag's commit SHA on all three runs.
- Rollback is real: tagging a prior known-good SHA deploys that exact artifact and SHA verifies it.
- Restore is real: re-tagging current main restores prod and SHA verifies correctly.

## State at close

- Prod serving: `build_sha=25f3b9d4be3d2733f5b81ab4fc9248f150e57037`
- Main HEAD: `25f3b9d4`
- Pipeline: all guards, health check, SHA verify, notify steps passing.
- Rollback tag: deleted.
