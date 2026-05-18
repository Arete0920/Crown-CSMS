# SOLOMON Phase 4A Preflight Gate (A0)

Status: Pre-Implementation Authorization Checkpoint

Purpose:
- Lock execution boundaries before any Phase 4A code changes.
- Prevent scope drift while moving from planning to bounded implementation.

## 1) Scope Decision

Approved target for first slice only:
- Review queue
- Review-state filtering

Deferred until re-gate:
- Stale detection automation
- Governance dashboard expansion
- Provenance hooks
- Version-lineage enhancements
- Metrics expansion

## 2) First Slice Boundaries

In scope for first implementation slice:
- Read/query surfaces for governance queue
- Deterministic filtering by review-relevant state
- Tenant-safe and RBAC-safe visibility behavior
- Fail-closed handling for invalid filters

Out of scope for first implementation slice:
- Notification systems
- Approval engines
- Workflow automation
- Cross-module orchestration
- UI redesign

## 3) Allowed File Scope (First Slice)

Implementation may modify only:
- backend/solomon/services.py
- backend/solomon/views.py
- backend/solomon/serializers.py
- backend/solomon/tests/*
- backend/crown_api/settings.py (only if a governance flag is explicitly approved)
- docs/solomon/*

Any other path requires explicit approval before edit.

## 4) Explicitly Prohibited Changes

Prohibited for first slice:
- Root URL rewiring outside existing SOLOMON surfaces
- Onboarding workflow mutation
- Migration-heavy model redesign
- Frontend changes
- Package/lockfile changes
- Auth/RBAC/tenant architecture rewiring
- Deployment/Azure/GitHub workflow changes

## 5) Success Criteria (Must All Pass)

Functional:
- Governance queue returns deterministic ordering.
- Review-state filters return deterministic subsets.
- Invalid filter input fails closed (safe empty response).

Safety:
- Tenant isolation holds for all queue/filter responses.
- RBAC visibility constraints remain enforced.
- Existing SOLOMON and onboarding paths remain unaffected.

## 6) Required Tests

New or updated tests required in first slice:
- Queue ordering determinism tests
- Review-state filter correctness tests
- Invalid filter fail-closed tests
- Tenant isolation tests
- RBAC visibility tests
- Regression tests for existing SOLOMON APIs/adapters

Validation commands:
- python3 backend/manage.py test solomon --keepdb
- python3 backend/manage.py test onboarding.tests --keepdb
- python3 backend/manage.py check

## 7) Migration Rules

First slice default:
- No schema migration unless strictly required.
- If migration is required, it must be additive, minimal, and pre-approved.

## 8) Flag and Rollback Rules

Flags:
- Existing SOLOMON flags remain authoritative.
- New governance flag is optional and only if explicitly approved.

Rollback:
- Flag disable path must restore previous behavior without workflow interruption.
- No irreversible behavior in first slice.

## 9) Commit Gate

No commit unless all are true:
- Changes stay inside approved first-slice paths.
- Required tests pass.
- Django check passes.
- No prohibited changes introduced.
- Diff reviewed against first-slice scope.

## 10) Authorization Record

Decision:
- [ ] Approve Phase 4A first slice implementation now
- [ ] Hold at planning checkpoint

If approved now:
- Authorized slice: Review queue + review-state filtering only
- Authorized paths: as listed above
- Next gate: Re-authorization before stale-detection/dashboard expansion
