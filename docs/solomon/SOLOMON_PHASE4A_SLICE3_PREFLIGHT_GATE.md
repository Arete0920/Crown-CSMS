# SOLOMON Phase 4A Slice 3 — Preflight Gate

Status: Pre-Implementation Authorization Checkpoint

Purpose:
- Lock Track A implementation boundaries before any Slice 3 code changes.
- Prevent premature governance authority escalation into enforcement territory.
- Preserve human governance ownership during initial signal detection work.

Authorized Track:
- Track A only (stale thresholds, backlog aging, orphaned-resource detection)

Explicitly not authorized in this gate:
- Track B (scope-drift detection — gated on ResourceVersion coverage audit)
- Track C (audit telemetry model, lifecycle transition enforcement — design only)


## 1) Scope Decision

Approved for Slice 3 implementation:
- Stale-content threshold detection (warning and stale buckets)
- Review backlog aging measurement (queue depth and age buckets)
- Orphaned-resource detection (no category, no audience, no route/module linkage)

All three signals are ADVISORY ONLY.
No signal in this slice carries enforcement authority.
No signal in this slice may mutate SolomonResource state.

Deferred until re-gate:
- Governance audit telemetry persistence (SolomonAuditEvent or equivalent)
- Lifecycle transition enforcement at any layer
- Visibility mismatch auto-correction or flagging
- Scope-drift detection (requires D3 ResourceVersion audit first)
- Tenant-scope drift enforcement
- Unpublished-content aging signals (advisory; deferred pending threshold validation)


## 2) Governance Signal Authority Boundary

This rule is absolute for all Slice 3 implementation work:

Signals may:
- Detect a condition
- Score severity (warning / stale / critical)
- Annotate a queryset with a derived classification
- Report a count or list for governance review
- Queue a resource for human review

Signals must not:
- Transition a resource lifecycle state
- Change resource visibility
- Auto-expire or auto-archive any resource
- Auto-correct any field on SolomonResource or any related model
- Write any record to a persistence layer (no event writes, no audit inserts)

Any service function that could mutate SolomonResource or a related model
is out of scope for Slice 3 and must not be written.


## 3) Allowed File Scope

Implementation may modify only:
- backend/solomon/services.py (new detection query functions only)
- backend/solomon/tests/test_governance_signals.py (new; Track A tests only)
- docs/solomon/* (documentation updates)

Implementation must not touch:
- backend/solomon/models.py
- backend/solomon/migrations/*
- backend/solomon/views.py (no new API endpoints in Slice 3)
- backend/solomon/serializers.py
- backend/solomon/admin.py
- backend/crown_api/settings.py
- Any path outside backend/solomon/ and docs/solomon/

Any expansion beyond the allowed file scope requires an explicit new gate
before the edit is made. This rule has no exceptions.


## 4) Implementation Boundaries Per Signal

### 4A — Stale-Content Detection

Allowed:
- A service function that accepts a queryset and returns resources classified
  as warning or stale based on review_date and created_at.
- Parameterized thresholds (warning_days, stale_days) with fail-closed behavior
  on invalid input.
- Returns a queryset or annotated queryset; never modifies records.

Guidance:
- Follow the pattern of governance_stale_review_queue() already in services.py.
- Stale detection for Slice 3 may extend or parallel that function.
- Do not consolidate or replace existing stale queue functions without
  explicit approval.

Not allowed:
- Any write to review_date or updated_at.
- Any status mutation.
- Any model save call.

### 4B — Review Backlog Aging

Allowed:
- A service function that returns queue depth and aging buckets
  (0–14 / 15–45 / 46–90 / 90+ days) as a structured read-only result.
- Oldest unactioned item age as a derived value.
- Fail-closed on invalid bucket parameters.

Not allowed:
- Escalation signals that change resource state based on backlog age.
- Any write.

### 4C — Orphaned-Resource Detection

Allowed:
- A service function that returns resources with no category linkage,
  no audience assignment, and no module or route_path, filtered by
  status (published, approved, or both).
- Parameterized by status argument; fail-closed on invalid status.

Not allowed:
- Any auto-archival or soft-delete logic.
- Any field mutation on detected resources.
- Any cascade action.


## 5) D-Decision Status at Gate Entry

| Decision | Status         | Resolution                                          |
|----------|----------------|-----------------------------------------------------|
| D1       | Resolved       | Append-only isolated event model; no runtime coupling|
| D2       | Resolved       | Service-layer enforcement only; no model hooks       |
| D3       | Unresolved     | ResourceVersion audit required before drift work    |
| D4       | Resolved       | Visibility mismatch advisory-only; no auto-correct  |

D3 unresolved status does not block Track A. It blocks Track B only.
D1 and D2 resolutions constrain Track C design but do not block Track A.


## 6) Prohibited Changes

Prohibited for entire Slice 3 duration:
- New Django migrations
- New model fields or model class additions (SolomonAuditEvent is Track C)
- New API views or URL patterns
- Frontend changes of any kind
- Notification or messaging integrations
- Auth, RBAC, or tenant architecture changes
- Deployment, CI/CD, or workflow file changes
- Package or lockfile changes
- Any model save() or clean() hook modifications
- Auto-remediation logic of any kind


## 7) Success Criteria (All Must Pass Before Slice 3 Close)

Functional:
- Stale detection returns correct warning and stale classifications
  for parameterized thresholds.
- Backlog aging returns correct depth and bucket counts for known fixtures.
- Orphaned detection returns correct resource sets for status-filtered input.
- All three functions fail closed on invalid parameters.

Safety:
- No SolomonResource records are modified by any Slice 3 function.
- No database writes occur from any Slice 3 detection function.
- Tenant isolation holds for all detection query results.
- RBAC visibility constraints are preserved in all detection queries.
- All existing 68 SOLOMON tests continue to pass.

Gate:
- python backend/manage.py test solomon --keepdb passes with 0 failures.
- python backend/manage.py check reports 0 issues.
- git diff --stat from 462de7a8 shows only allowed file paths.


## 8) Required Tests (test_governance_signals.py)

New tests required before Slice 3 may close:

Stale detection:
- Warning threshold: resources at warning boundary are correctly classified.
- Stale threshold: resources at stale boundary are correctly classified.
- Below threshold: resources not yet warning are excluded.
- Invalid threshold parameters fail closed.
- No model writes occur during detection (confirm via queryset inspection).

Backlog aging:
- Correct bucket assignment for items in each age range.
- Oldest item age is returned correctly.
- Empty queue returns zero counts with no errors.
- Invalid bucket parameter fails closed.

Orphaned detection:
- Published resource with no category, no audience, no route is detected.
- Approved resource with no linkage is detected.
- Draft resource with no linkage after 30 days is flagged.
- Resource with at least one valid linkage is excluded.
- Invalid status parameter fails closed.


## 9) Bootstrap Verification (Run Before Writing First Line)

Required clean state before any Slice 3 implementation begins:

  python backend/manage.py test solomon --keepdb
  python backend/manage.py check
  git status --short --branch
  git log --oneline -3

Expected state:
- All 68 tests pass.
- 0 check issues.
- Branch: solomon/start, HEAD at 462de7a8 or later clean commit.
- Working tree clean (no uncommitted changes).

If any condition fails, resolve before writing implementation code.
