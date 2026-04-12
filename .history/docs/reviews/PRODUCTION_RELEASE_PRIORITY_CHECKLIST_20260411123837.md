# Production Release Priority Checklist

## Scope

This checklist captures the next highest-priority work for moving the full Crown platform toward a production-ready release after the Compass / Discernment audit and runtime isolation passes.

## Completed in This Pass

- Removed the hardcoded Django `SECRET_KEY` fallback from `backend/crown_api/settings.py`
- Replaced it with a production-safe guard that requires `DJANGO_SECRET_KEY` / `SECRET_KEY` outside local debug
- Re-verified the file with `py_compile`

## Current Verification Evidence

Most recent command run:

```powershell
python -m py_compile backend/crown_api/settings.py
python backend/manage.py check --deploy
```

Observed result:

- `settings.py` compiles cleanly
- The hardcoded secret warning is gone
- `check --deploy` still reports a large number of warnings, dominated by:
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

**Reduce the `check --deploy` warning burden by cleaning up high-value DRF schema/serializer gaps and then rerun the deployment checks.**

## Release Readiness Summary

The platform is safer than before and the top secret-management blocker has been addressed, but the full release still needs:

- deployment-environment verification
- schema/API cleanup
- broader regression evidence
- formal release gating

