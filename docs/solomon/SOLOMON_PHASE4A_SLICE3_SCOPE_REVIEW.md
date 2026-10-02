# SOLOMON Phase 4A Slice 3 — Governance Metrics & Drift Detection Scope Review

Status: Design Phase — No Implementation Authorized

Purpose:
- Define governance signals that matter for operational visibility.
- Define what constitutes drift within SOLOMON-governed content.
- Define thresholds, measurement intent, and governance meaning.
- Establish allowed future implementation boundaries.
- Lock the advisory vs. authoritative distinction before any code is written.

This document is a scope review only. No implementation is approved until a
separate preflight gate is passed and a bounded implementation plan is authored.


## 1. Governance Signal Inventory

### 1.1 Stale-Content Thresholds

Signal:
- A resource or playbook that has exceeded its expected review cycle without
  a completed review action.

Governance meaning:
- Content may no longer reflect current policy, program structure, or audience need.
- Does not mean content is wrong; means confidence in accuracy is degraded.

Proposed thresholds (advisory; requires ALR confirmation before hardening):
- Warning window: review_date more than 75 days ago, or review_date null with
  created_at more than 75 days ago.
- Stale window: review_date more than 90 days ago, or review_date null with
  created_at more than 90 days ago.
- Critical: stale threshold exceeded for published or approved content with
  no assigned owner.

Already implemented:
- governance_stale_review_queue() in services.py covers warning and stale buckets.
- Thresholds are parameterized (warning_days, stale_days) and fail-closed.

Remaining scope for Slice 3:
- Validate thresholds against actual content lifecycle expectations.
- Confirm whether published-only, approved-only, or both statuses should
  trigger stale detection in all buckets.
- Define whether review_date null is always stale or only after a grace period.

---

### 1.2 Orphaned-Resource Detection

Signal:
- A resource exists with no active category linkage, no audience assignment,
  and no route_path or module assignment.

Governance meaning:
- Resource cannot be surfaced through any governed consumption path.
- Orphaned resources represent governance debt: they exist in the system but
  cannot be verified, reviewed, or retired through normal workflow.

Thresholds:
- Any resource with status=published or status=approved that has no category,
  no audiences, and no module or route_path is orphaned.
- Draft resources with no category after 30 days are governance-flagged
  (not blocked; flagged for review).

Advisory vs. authoritative:
- ADVISORY: orphaned detection should surface as a governance signal only.
- Orphaned resources must NOT be auto-archived or auto-deleted under any
  Slice 3 implementation.
- Remediation is a human governance action.

Deferred:
- No automated remediation.
- No cascade delete or status mutation from orphan detection.

---

### 1.3 Visibility Mismatch Detection

Signal:
- A resource or playbook whose visibility setting is inconsistent with its
  assigned audience scope or tenant scope.

Examples of mismatches:
- visibility=public but scope=school (school-scoped content should not be
  globally visible by default).
- visibility=staff but audiences include is_public=True audience entries.
- visibility=restricted but route_path is a top-level public route.

Governance meaning:
- Content may be over-exposed or under-exposed relative to its intended audience.
- Neither condition is automatically harmful, but both require human review.

Thresholds:
- Any resource where visibility and scope combination is in the mismatch matrix
  should be flagged for governance review.
- Mismatch matrix to be defined in a future ALR checkpoint before implementation.

Advisory vs. authoritative:
- ADVISORY ONLY for Slice 3.
- No visibility mutations from detection logic.
- Flagging is read-only and surfaced as a governance signal.

---

### 1.4 Unpublished-Content Aging

Signal:
- A resource has been in draft or approved state for an extended period without
  a lifecycle transition to published or archived.

Governance meaning:
- Content may be abandoned, blocked in a workflow, or waiting on a reviewer
  who is no longer engaged.
- Long-dwelling draft and approved content creates review queue noise and
  reduces governance confidence.

Proposed thresholds (advisory):
- Draft aging warning: 45 days in draft with no update to updated_at.
- Draft aging stale: 90 days in draft with no update.
- Approved aging warning: 30 days approved with no publish action.
- Approved aging stale: 60 days approved with no publish action.

These thresholds differ from stale-content thresholds, which measure content
accuracy relative to review_date. Aging thresholds measure workflow velocity.

Advisory vs. authoritative:
- ADVISORY for Slice 3.
- No forced lifecycle transitions from aging detection.
- Detection surfaces as a governance queue signal; human action required.

---

### 1.5 Tenant-Scope Drift

Signal:
- Content originally scoped to one tenant boundary (school, organization, global)
  has had its scope field modified without a corresponding governance review.

Governance meaning:
- Scope widening (e.g., school → global) without review may expose
  school-specific content to unintended audiences.
- Scope narrowing (e.g., global → school) without review may suppress
  content that other tenants depend on.

Detection approach:
- Requires audit trail of scope field changes per resource.
- SolomonResourceVersion can capture scope at version creation time.
- Drift is detectable as: current resource.scope differs from the scope
  recorded in the most recent SolomonResourceVersion.

Advisory vs. authoritative:
- ADVISORY for Slice 3.
- Detection requires ResourceVersion logging to be consistent; this must be
  validated before any drift signal is surfaced.

Deferred dependency:
- Version logging completeness audit must precede any scope-drift detection.
- This may push scope drift to Slice 4 depending on version coverage findings.

---

### 1.6 Review Backlog Aging

Signal:
- The governance review queue contains items that have not been actioned
  within expected review-cycle windows.

Governance meaning:
- Backlog accumulation is an operational health signal.
- A growing unactioned backlog means governance workflows are under-resourced
  or blocked, not that content is wrong.

Proposed measurements (advisory):
- Queue depth: count of draft + approved resources at any given time.
- Aging buckets: 0–14 days (fresh), 15–45 days (aging), 46–90 days (stale),
  90+ days (critical backlog).
- Oldest unactioned item age: single most actionable governance metric.

Advisory vs. authoritative:
- ADVISORY for Slice 3.
- No SLAs enforced by system logic.
- Metrics surfaced for human governance operations only.

---

### 1.7 Governance Audit Telemetry

Signal:
- A queryable record of governance-relevant lifecycle transitions: who took
  what action on which resource, and when.

Governance meaning:
- Required for institutional accountability.
- Enables post-hoc audit of: who published what, who approved what,
  who archived what, and when review cycles were completed.

Current state:
- SolomonResource tracks created_at, updated_at, owner, approver, review_date.
- No explicit event log for lifecycle transitions exists in Phase 2 models.

Scope for Slice 3 (design only):
- Define which lifecycle events require explicit audit records.
- Define minimum audit record fields: resource_id, action, actor, timestamp,
  previous_status, new_status.
- Determine whether audit records live in a new SolomonAuditEvent model
  or leverage the existing crown_api AuditEvent infrastructure.

Advisory vs. authoritative:
- Design decision required: isolated SOLOMON audit model vs. shared audit
  infrastructure.
- This decision has architectural implications and must not be made
  unilaterally in implementation.
- Requires explicit ALR checkpoint before any model changes.

Deferred:
- No new models in Slice 3.
- No audit event writes in Slice 3.
- Design only.

---

### 1.8 Lifecycle Transition Integrity

Signal:
- A resource has undergone a lifecycle transition that violates the defined
  allowed transition graph.

Allowed transition graph (from SOLOMON_GOVERNANCE_MODEL):
- draft → approved
- approved → published
- published → archived
- any → draft (rollback, explicit only)
- archived → draft (re-open, explicit only)

Invalid transitions (must not be permitted):
- draft → published (bypasses approval gate)
- approved → draft without explicit rollback intent
- archived → published (requires re-entry through draft/approved)

Current state:
- No transition enforcement exists in Phase 2 models; status is a CharField
  with no validation beyond choice constraints.
- Invalid transitions are currently possible via direct field write.

Scope for Slice 3 (design only):
- Define where transition enforcement belongs: model clean(), service layer,
  or serializer validation.
- Define whether invalid transitions should raise hard errors or emit
  governance signals.
- Preference: enforce at service layer for API surfaces, advisory signal
  for admin surfaces.

Advisory vs. authoritative:
- AUTHORITATIVE enforcement is the correct long-term posture for transition
  integrity.
- However, enforcement must not be implemented in Slice 3 without migration
  path for any existing content in non-conforming states.
- Slice 3 output: design spec only. Enforcement moves to Slice 4+ with
  pre-implementation data audit.


## 2. Advisory vs. Authoritative Classification

| Signal                          | Slice 3 Posture | Long-Term Posture     |
|---------------------------------|-----------------|-----------------------|
| Stale-content thresholds        | Advisory        | Advisory              |
| Orphaned-resource detection     | Advisory        | Advisory              |
| Visibility mismatch detection   | Advisory        | Advisory              |
| Unpublished-content aging       | Advisory        | Advisory              |
| Tenant-scope drift              | Advisory        | Advisory              |
| Review backlog aging            | Advisory        | Advisory              |
| Governance audit telemetry      | Design only     | Authoritative record  |
| Lifecycle transition integrity  | Design only     | Authoritative enforce |

Advisory signals surface information for human governance action.
Authoritative signals block or record actions at the system level.
No advisory signal in this review should be upgraded to authoritative
without an explicit ALR decision.


## 3. Explicit Deferrals

The following remain out of scope through Slice 3 and must not be introduced
during any Slice 3 implementation work:

- Governance dashboards (UI or API aggregation endpoints)
- Notification systems (email, in-app, Teams)
- Automated approval or rejection logic
- Auto-archival or auto-remediation of any kind
- Automated scoring or semantic prioritization of review items
- Cross-module orchestration from governance signals
- Curriculum ingestion or alignment signals
- User-facing analytics or reporting surfaces
- SLA enforcement on review cycle times


## 4. Implementation Boundary

Slice 3 produces this scope review document only.

Any implementation work under Slice 3 is explicitly not authorized by this
document. Implementation requires:

1. A separate Phase 4A Slice 3 Preflight Gate document.
2. Explicit bounded file scope (following SOLOMON_PHASE4A_PREFLIGHT_GATE.md
   conventions).
3. A passing bootstrap verification run:
   - python backend/manage.py test solomon --keepdb
   - python backend/manage.py check
   - git status --short --branch confirming clean state from 462de7a8


## 5. Recommended Next Decision Points

Before any Slice 3 implementation is authorized, the following must be resolved:

D1 — Audit telemetry model placement: isolated SolomonAuditEvent or shared
     crown_api AuditEvent infrastructure? (Architectural decision. ALR required.)

D2 — Transition integrity enforcement layer: model, service, or serializer?
     (Design decision. No model changes without migration path audit.)

D3 — Scope drift detection dependency: is SolomonResourceVersion logging
     complete enough to support drift detection, or must coverage be audited
     first? (Operational readiness check. Precedes any drift signal work.)

D4 — Visibility mismatch matrix: define the full set of visibility/scope
     combination rules before any detection logic is written.
     (Governance definition. Human decision required.)

These four decisions are blocking for Slice 3 implementation in the areas
they cover. Signals that have no blocking dependencies (stale thresholds,
backlog aging, orphaned detection) may proceed to preflight gate independently.
