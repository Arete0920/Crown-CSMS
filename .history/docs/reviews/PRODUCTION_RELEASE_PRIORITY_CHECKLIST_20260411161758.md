# Production Release Priority Checklist

## Scope

This checklist captures the next highest-priority work for moving the full Crown platform toward a production-ready release after the Compass / Discernment audit and runtime isolation passes.

## Completed in This Pass

- Removed the hardcoded Django `SECRET_KEY` fallback from `backend/crown_api/settings.py`
- Replaced it with a production-safe guard that requires `DJANGO_SECRET_KEY` / `SECRET_KEY` outside local debug
- Fixed non-local DEBUG resolution so explicit `DJANGO_DEBUG=0` / `DEBUG=0` is now honored correctly in CI and release workflows
- Aligned `deploy-prod.yml`, `deploy-prod-dispatch.yml`, and `rc-runbook.yml` to run release checks with `DJANGO_ENV=production` and `CROWN_ENV=prod`
- Confirmed the HSTS / SSL redirect settings are active under production-style envs, eliminating the prior `security.W004` / `security.W008` warnings in verification runs
- Added targeted schema coverage for governance, signals, board oversight, system, director, dashboard, analytics, exports, finance APIs, and multiple wizard/API clusters
- Cleared additional warning groups across academic year, attendance, billing, comms, course catalog, fee schedule, financial aid, grade scale/weights, guardian-household setup, remaining wizard endpoints, and several aftercare/aid/billing/comms/advancement surfaces
- Ran the backend release regression bundle successfully: `11 passed, 1 warning in 92.52s`
- Ran the frontend hygiene audit and production build successfully via `tools/audit_frontend.ps1`
- Ran targeted production-flag tests successfully: `9 passed in 0.03s`
- Re-verified the updated release surface with repeated `py_compile` and fresh `check --deploy` evidence after each cleanup batch

## Current Verification Evidence

Most recent commands run:

```powershell
python -m py_compile backend/crown_api/settings.py backend/governance/openapi.py backend/governance/views.py backend/signals/api.py backend/board_oversight/api_governance.py backend/board_oversight/views.py backend/crown_api/system_views.py backend/crown_api/director_views.py backend/crown_api/dashboards/views.py
python docs/release/release_closeout/run_release_pytests.py
./tools/audit_frontend.ps1
pytest backend/crown_api/tests/test_prod_flag_guards.py -q
$env:DJANGO_SECRET_KEY='ci-not-secret'; $env:DJANGO_DEBUG='0'; $env:DJANGO_ENV='production'; $env:CROWN_ENV='prod'; python backend/manage.py check --deploy
```

Observed result:

- `settings.py`, governance OpenAPI wiring, signals API files, board oversight views, director/dashboard surfaces, analytics/export endpoints, finance APIs, and the latest wizard groups all compile cleanly
- The hardcoded secret fallback is gone
- The non-local DEBUG parsing and prod-env resolution are covered by targeted tests: `9 passed in 0.03s`
- Release regression bundle passed: `11 passed, 1 warning in 92.52s`
- Frontend hygiene audit and production build passed successfully
- Repo-side production evidence still shows `DEBUG=False`, `DJANGO_DEBUG=0`, `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS` in `prod_appsettings_before.json`, with secret values redacted
- The Azure drift watchdog workflow already enforces that production `SECRET_KEY` and `DB_PASSWORD` remain Key Vault-backed references
- With explicit production-style env settings (`DJANGO_DEBUG=0`, `DJANGO_ENV=production`, `CROWN_ENV=prod`, `DJANGO_SECRET_KEY=...`), the warning baseline improved in verified steps from `424` → `395` → `361` → `335` → `307` → `279` → `259` → **`235`** issues
- In the same verified runs, `drf_spectacular.W002` occurrences dropped from `323` earlier to `209` → `181` → `156` → **`132`**
- `security.W018`, `security.W004`, and `security.W008` are no longer present in the captured production-style verification output
- The remaining deployment warnings are still dominated by:
  - `drf_spectacular.W002` serializer/schema gaps across the smaller remaining API clusters
  - static-analysis debt in older runtime-heavy files such as `director_views.py` and a few complex wizard helpers

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

**Continue the remaining schema/API cleanup from the now much lower baseline, focusing next on the still-unresolved drf-spectacular clusters that remain after the wizard, aftercare, aid, billing, comms, and advancement passes.**

## Release Readiness Summary

The platform is safer than before and the top secret-management blocker has been addressed. Backend regression and frontend build proof are now in hand, but the full release still needs:

- deployment-environment verification
- remaining schema/API cleanup in the smaller leftover endpoint clusters
- formal release gating
- operational signoff in the target release window
- final disposition of older static-analysis debt that is not currently blocking runtime verification
