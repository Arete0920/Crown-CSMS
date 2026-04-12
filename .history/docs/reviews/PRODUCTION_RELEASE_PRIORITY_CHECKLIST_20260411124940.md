# Production Release Priority Checklist

## Scope

This checklist captures the next highest-priority work for moving the full Crown platform toward a production-ready release after the Compass / Discernment audit and runtime isolation passes.

## Completed in This Pass

- Removed the hardcoded Django `SECRET_KEY` fallback from `backend/crown_api/settings.py`
- Replaced it with a production-safe guard that requires `DJANGO_SECRET_KEY` / `SECRET_KEY` outside local debug
- Added targeted schema coverage for governance and signals endpoints to reduce high-value `drf_spectacular.W002` warnings
- Ran the backend release regression bundle successfully: `11 passed, 1 warning in 92.52s`
- Ran the frontend hygiene audit and production build successfully via `tools/audit_frontend.ps1`
- Re-verified the updated release surface with `py_compile` and a fresh `check --deploy`

## Current Verification Evidence

Most recent commands run:

```powershell
python -m py_compile backend/crown_api/settings.py backend/governance/openapi.py backend/governance/views.py backend/signals/api.py
python docs/release/release_closeout/run_release_pytests.py
./tools/audit_frontend.ps1
python backend/manage.py check --deploy
```

Observed result:

- `settings.py`, governance OpenAPI wiring, and signals API files compile cleanly
- The hardcoded secret fallback is gone
- Release regression bundle passed: `11 passed, 1 warning in 92.52s`
- Frontend hygiene audit and production build passed successfully
- `check --deploy` still reports warning debt, but the fresh local count dropped from `432` to `426` issues and `drf_spectacular.W002` occurrences are now `323`
- The remaining deployment warnings are still dominated by:
  - `drf_spectacular.W002` serializer/schema gaps across many APIViews
  - local-environment security warnings because `DEBUG=True` in the current local session

## Priority Order

### 1. Production config and environment validation

Focus:

- verify production env vars are present in Azure / deployment targets
- confirm `DJANGO_SECRET_KEY` is set everywhere non-local
- confirm `DEBUG=False` in all release environments
- confirm HTTPS / cookie / HSTS settings behave correctly in the real deployment environment

### 2. API schema and serializer coverage cleanup

Focus:

- reduce `drf_spectacular.W002` warnings
- add missing `serializer_class` / schema metadata for high-value APIViews
- improve release confidence in published API contracts

### 3. Full regression and smoke test pass

Focus:

- backend regression suite
- frontend build and smoke verification
- major role-based workflows
- module-by-module acceptance for admissions, finance, academics, aid, attendance, discipline, comms, and governance

### 4. Core invariants and release gating

Focus:

- tenant isolation proofs
- finance / ledger invariants
- audit logging verification
- migration consistency
- release-candidate gate signoff

### 5. Governance and analytics maturity

Focus:

- keep Discernment default-off until explicitly approved
- keep Compass explainable and governable
- avoid overstating predictive readiness in board/governance surfaces

## Immediate Next Recommended Work Item

**Verify the non-local release configuration (`DJANGO_SECRET_KEY`, `DEBUG=False`, HTTPS/cookie behavior) and continue the remaining schema cleanup from the now-lower warning baseline.**

## Release Readiness Summary

The platform is safer than before and the top secret-management blocker has been addressed. Backend regression and frontend build proof are now in hand, but the full release still needs:

- deployment-environment verification
- remaining schema/API cleanup
- formal release gating
- operational signoff in the target release window
