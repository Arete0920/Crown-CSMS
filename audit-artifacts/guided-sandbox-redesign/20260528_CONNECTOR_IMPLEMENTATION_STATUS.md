# Guided Sandbox Redesign - Connector Implementation Status

Date: 2026-05-28
Repository: tcmegahan/Crown2026
Scope: Work completed through GitHub connector without local runtime or deployed environment access

## Executive status

Implementation status: IN PROGRESS
Buyer-facing readiness: NOT VERIFIED
Release posture: NO-GO until runtime, build, seed/reset, role, and tenant-isolation proof pass

This artifact records what was implemented from the connector and what remains blocked on runtime/deployment verification.

## Completed through connector

### Strategy and policy

- Created Guided Proof Sandbox product blueprint.
- Converted sandbox data policy from pending to active.
- Added school, daycare / early learning, and camp demo tracks.
- Defined guided and self-guided evaluator modes.
- Added evaluator-loop operating design.
- Added invite, feedback, and analytics implementation contract.

### Frontend scaffolding

- Added `frontend/dashboards/src/sandbox/sandboxExperience.js`.
- Added `frontend/dashboards/src/pages/SandboxLandingPage.jsx`.
- Added `frontend/dashboards/src/sandbox/SandboxCommandCenter.jsx`.
- Added `frontend/dashboards/src/sandbox/sandboxTelemetry.js`.
- Added tests for sandbox catalog and command-center behavior.

### Backend scaffolding

- Added `backend/core/management/commands/sandbox_seed.py`.
- Added `backend/core/management/commands/sandbox_verify.py`.
- Commands currently validate manifests and contract prerequisites only. They do not write model data yet.

### Seed-pack baseline

- Added school manifest: `sandbox/seed_packs/school/heritage_core/manifest.json`.
- Added daycare manifest: `sandbox/seed_packs/daycare/emmanuel_early_learning/manifest.json`.
- Added camp manifest: `sandbox/seed_packs/camp/cedar_ridge_summer_camp/manifest.json`.

### Safety and gate scripts

- Added `scripts/execution/210_apply_guided_sandbox_frontend_patch.ps1`.
- Added `scripts/execution/211_sandbox_no_real_data_scan.ps1`.
- Added `scripts/execution/212_sandbox_gate_check.ps1`.

## Not completed through connector

The following are not completed because they require runtime access, local build execution, deployed environment access, or deeper model-specific implementation.

| Area | Status | Reason |
| --- | --- | --- |
| `/sandbox` route live verification | NOT VERIFIED | Requires patch execution and frontend build/runtime proof |
| Login query-param behavior live verification | NOT VERIFIED | Requires patch execution and frontend tests |
| Frontend build | NOT VERIFIED | No local or CI execution was run from connector |
| Unit tests | NOT VERIFIED | Test files were added, but not executed |
| Backend command execution | NOT VERIFIED | Management commands were added, but not run |
| Deterministic model-level seed writes | NOT DONE | Requires model-specific implementation per module |
| Full reset and scenario reset | NOT DONE | Requires database-write implementation and runtime verification |
| Expected metric assertions against dashboards | NOT DONE | Requires seeded data and API/dashboard verification |
| Persona login proof | NOT VERIFIED | Requires authenticated runtime test |
| Cross-tenant isolation proof | NOT VERIFIED | Requires runtime/authenticated negative tests |
| Invite-token backend | NOT DONE | Contract added; models/API not implemented yet |
| Feedback backend | NOT DONE | Contract added; models/API not implemented yet |
| Privacy-safe analytics backend | NOT DONE | Frontend helper added; backend endpoint not implemented |
| Deployed smoke test | NOT VERIFIED | Requires deployed environment access |

## Required next commands in repo workspace

Run from repository root after pulling latest changes:

```powershell
# Wire route/login changes into established frontend files.
powershell -ExecutionPolicy Bypass -File scripts/execution/210_apply_guided_sandbox_frontend_patch.ps1

# Run static sandbox data safety scan.
powershell -ExecutionPolicy Bypass -File scripts/execution/211_sandbox_no_real_data_scan.ps1

# Run static guided sandbox gate check.
powershell -ExecutionPolicy Bypass -File scripts/execution/212_sandbox_gate_check.ps1
```

Then run the frontend/backend test commands used by the current repo standard.

## Required management command checks

After dependencies and Django settings are available:

```bash
python manage.py sandbox_seed --track school --pack heritage_core --dry-run
python manage.py sandbox_seed --track daycare --pack emmanuel_early_learning --dry-run
python manage.py sandbox_seed --track camp --pack cedar_ridge_summer_camp --dry-run
python manage.py sandbox_verify --track school --pack heritage_core
python manage.py sandbox_verify --track daycare --pack emmanuel_early_learning
python manage.py sandbox_verify --track camp --pack cedar_ridge_summer_camp
```

Strict mode should fail until model-level writes, role proof, dashboard metric assertions, and tenant-isolation proof are implemented.

## Required release gates before buyer-facing use

| Gate | Required status |
| --- | --- |
| `/sandbox` route renders | PASS |
| Landing page shows school/daycare/camp tracks | PASS |
| Guided and self-guided modes visible | PASS |
| Login preselects role and school from query params | PASS |
| Demo-data warning visible on landing and login | PASS |
| Authenticated command center visible after login | PASS |
| Seed packs create deterministic data | PASS |
| Reset restores expected metrics | PASS |
| Persona permissions verified | PASS |
| Cross-tenant isolation verified | PASS |
| Feedback submission works | PASS |
| Invite expiration/revocation works | PASS |
| Analytics captures only allowed metadata | PASS |
| No-real-data scan passes | PASS |
| Compliance/customer-readiness artifacts reviewed | PASS |

## Current decision

NO-GO for external buyer-facing self-guided sandbox.

Acceptable next use:

- Internal review of scaffolded files
- Local patch execution
- Local build/test cycle
- Runtime integration work
- Development of model-specific seed/reset writes

Not acceptable yet:

- Sending `/sandbox` to prospects
- Claiming daycare/camp demos are fully working
- Claiming self-guided access is production-ready
- Claiming seed/reset, tenant isolation, or role proof is complete
