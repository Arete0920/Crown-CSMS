# SOLOMON Phase 4 Governance Execution Plan

Status: Planning Only

This document defines the bounded execution blueprint for Phase 4.

Scope intent:
- Planning checkpoint only
- No implementation in this phase document task
- No migrations in this phase document task
- No admin modifications in this phase document task

## 1. Phase 4 objectives

Primary objective:
- Scale SOLOMON governance operations safely before scaling content volume.

Phase 4 outcomes to enable:
- Operational review queues for governance work
- Review-state filtering for governed content operations
- Stale review detection for lifecycle hygiene
- Governance dashboards for operational visibility

Architecture principles retained:
- SOLOMON augments workflows and does not own workflows
- Fail-closed behavior for optional governance surfaces
- Tenant and RBAC boundaries remain preserved
- Read-only usage remains non-blocking for core execution paths

## 2. P4-A scope boundaries

P4-A is intentionally narrow and limited to governance operations proof.

In scope:
- Review queue
- Review-state filtering
- Stale review detection
- Governance dashboards

Out of scope for P4-A:
- Generalized moderation systems
- Notifications
- Workflow automation
- Approval engines
- Cross-product orchestration
- Broad UX redesign

## 3. Allowed file scope

Execution scope for future P4-A implementation should be limited to:
- backend/solomon/models.py
- backend/solomon/serializers.py
- backend/solomon/services.py
- backend/solomon/views.py
- backend/solomon/admin.py
- backend/solomon/tests/*
- backend/crown_api/settings.py
- docs/solomon/*

Any expansion beyond these paths requires explicit approval before implementation.

## 4. Explicit prohibited changes

Prohibited without separate approval:
- Root URL expansion outside existing approved boundaries
- Onboarding workflow mutation
- Submission-path dependencies
- Frontend redesign work
- Package manifest changes
- Lock file changes
- Authentication model rewiring
- RBAC model rewiring
- Tenant isolation rewiring
- Production deployment config changes
- Azure resource changes
- Teams/SharePoint/publisher ingestion work
- Curriculum ingestion work
- AI/Copilot/semantic/vector integrations

## 5. Governance workflow model changes

Planned model-level governance additions for P4-A implementation:
- Review state normalization around lifecycle gates
- Explicit review ownership fields
- Review timestamps for auditability
- Last-reviewed markers to support stale detection

Constraints:
- Keep additions additive and backward-compatible
- Avoid introducing approval engines in P4-A
- Prefer existing lifecycle values and governance semantics

## 6. Admin workflow tooling

P4-A admin tooling target:
- Review queue list surfaces
- Filters by review state, lifecycle state, visibility, and scope
- Fast triage views for stale or unreviewed items
- Bulk-safe read/annotate operations only

Non-goals in P4-A:
- No notification pipelines
- No automated assignment engines
- No multi-step approval orchestration

## 7. Stale-content detection rules

Initial stale detection policy for P4-A:
- Flag published items with missing review markers
- Flag items past review threshold windows
- Flag lifecycle mismatch states (for example, published without review lineage)

Suggested threshold profile:
- Warning tier: approaching review due window
- Stale tier: exceeded due window

Behavior constraints:
- Detection is advisory and non-blocking in P4-A
- No automatic status transitions in P4-A

## 8. Review queue behavior

Queue behavior requirements:
- Deterministic ordering for repeatable triage
- Filter-first operation by state, scope, visibility, and owner
- No side effects from queue reads
- Explicit action logging for state changes

Safety requirements:
- Tenant-scoped queue outputs
- RBAC-respected visibility of queue items
- Fail-closed empty responses on invalid filters where applicable

## 9. Provenance/attribution future hooks

P4-A should introduce hooks only, not full ingestion pipelines.

Hook targets:
- Source attribution fields
- License metadata placeholders
- Provenance identifiers suitable for later publisher integrations
- Basic provenance validation boundaries for future enforcement

Non-goals now:
- No publisher sync
- No copyright adjudication engine
- No external ingestion integrations

## 10. Version lineage strategy

Lineage strategy goals:
- Record who changed content
- Record when change occurred
- Record why change occurred
- Preserve approval lineage references
- Support rollback eligibility assessment

P4-A constraints:
- Additive lineage tracking only
- No full rollback orchestration engine yet
- No cross-system lineage dependencies

## 11. Governance metrics strategy

Initial governance metrics for P4-A:
- Unpublished governed content count
- Stale review candidate count
- Orphaned resource count
- Visibility mismatch detections
- Scope compliance and tenant-audit signals

Dashboard behavior:
- Read-only aggregation surfaces
- Deterministic query definitions
- No alerting automation in P4-A

## 12. Required tests

Required verification for future P4-A implementation:
- Review queue filtering tests
- Review-state transition guard tests
- Stale detection rule tests
- Tenant isolation tests
- RBAC visibility tests
- Fail-closed behavior tests for invalid inputs/filters
- Governance metric calculation tests
- Regression tests for existing SOLOMON APIs and adapters

Baseline validation commands for implementation phase:
- python3 backend/manage.py test solomon --keepdb
- python3 backend/manage.py check

## 13. Migration constraints

Migration constraints for future implementation:
- Keep migrations additive and minimal
- No destructive schema edits
- No data-loss migrations
- No cross-app migration coupling without approval
- Provide reversible migration path where possible

For this planning checkpoint:
- No migrations are to be created or modified

## 14. Feature flag rules

Flag principles for P4-A implementation:
- Governance operations remain explicitly controllable
- Existing SOLOMON flags remain authoritative:
  - CROWN_SOLOMON_API_ENABLED
  - CROWN_SOLOMON_CONTEXT_ENABLED
- New governance-specific flags, if introduced, must default fail-closed

Runtime behavior rule:
- Disabled flags must produce silent noop or safe empty governance responses
- Core onboarding and workflow paths must remain operational

## 15. Commit gates

No implementation commit should pass unless all are true:
- Changes stay within explicitly approved file scope
- Review queue behavior is deterministic and tested
- Stale detection logic is deterministic and tested
- Tenant and RBAC tests pass
- Fail-closed behavior is verified
- Full SOLOMON test suite passes
- Django check passes
- No prohibited-scope drift detected

## 16. Rollback rules

Rollback policy for future P4-A implementation:
- Feature-flag rollback first
- Prefer operational disable over schema rollback
- Keep changes additive to simplify rollback safety
- Maintain backward compatibility for existing consumers

Rollback readiness requirement:
- Each P4-A increment must define a one-command disable path via flags

## 17. Phase sequencing map

Phase map after completion of P1 through P3B-B:
- P4-A: Governance Workflow Tooling (narrow proof)
- P4-B: Provenance and Attribution Hooks
- P4-C: Version Governance and Lineage Hardening
- P4-D: Governance Metrics and Drift Audits

Sequencing constraints:
- Complete and validate P4-A before expanding breadth
- Complete provenance and lineage controls before content-scale ingestion
- Defer Teams/SharePoint/publisher/curriculum/AI/semantic expansion until governance operations are stable and proven

---

Decision checkpoint intent:
- This document is the operational governance blueprint to execute before SOLOMON content scale begins.
