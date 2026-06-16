# Landmine audit remediation priority queue

Date: 2026-06-16
Branch: audit/landmine-reset-20260616
Base main SHA at branch creation: 568697c73cc30e97265b02728d706523376bd538

## Gate rule

Before additional module, dashboard, wizard, or admissions completion claims are accepted, the following work must be completed or explicitly tracked as NOT CERTIFIED.

## Priority 0 - Truth reset

1. Merge this audit artifact PR after checks are green.
2. Add admissions workflow as an explicit certification domain.
3. Update release/readiness language so admissions advanced workflow is NOT CERTIFIED.
4. Preserve NO-GO posture.

## Priority 1 - Current open module lanes

1. Re-verify Module 019 PR #1051 current-head checks before merge.
2. Rebuild Module 021 cleanly from current main after Module 019 settlement.
3. Recheck Module 016 PR #1047 after main has changed; do not merge stale matrix/scorecard content without rebasing or rebuilding cleanly.

## Priority 2 - Admissions remediation

Create a clean current-head admissions lane against `backend/applications`, not obsolete `backend/admissions` paths.

Required deliverables:

- explicit state transition service
- valid transition map
- invalid transition 409 response
- final submit idempotency guard
- duplicate prevention tests
- family status center API
- review/decision workflow with human-only decision guard
- decision reason and audit event capture
- waitlist governance workflow
- acceptance-to-enrollment continuity
- tenant and role-scoped tests

## Priority 3 - PROVEN module depth recheck

All 39 PROVEN modules must be rechecked for proof depth:

- implementation exists
- test exists
- test targets the real implementation path
- runtime/API/model/service wiring exists where applicable
- evidence cites current commit SHA
- scope boundary is explicit

## Priority 4 - Close 12 NOT_PROVEN modules

Official current gaps:

1. 016 Faculty Load & Scheduling
2. 019 Assessment & Testing Framework
3. 021 Competency Tracking
4. 024 Transportation & Routes
5. 025 Nutrition & Food Services
6. 026 After-School & Extended Care
7. 030 Student Portal
8. 031 Administrative Portal
9. 034 Fundraising & Giving
10. 037 Advanced Discipline Workflows
11. 039 Christian Formation & Tracking
12. 050 Business Intelligence Suite

## Priority 5 - Dashboard live-data certification

All 40 dashboards remain MAPPED until live-data validation proves:

- route loads
- role access works
- API endpoint exists
- endpoint returns live or deterministic seeded data
- UI renders the returned data
- empty/degraded/error states work
- evidence includes screenshot/API artifact

## Priority 6 - Wizard functional-flow certification

Route/API contract coverage is not enough. Each wizard must prove full role-scoped runtime completion before any release-ready claim.

## Priority 7 - Saved-chat and old-branch package quarantine

Any old package, saved chat export, closed PR, stale branch, or backlog document must be classified before reuse:

- CURRENT_HEAD_IMPLEMENTATION
- REQUIREMENTS_ONLY
- OBSOLETE_PATH
- DUPLICATE_ARCHITECTURE
- REJECT

No old package may be bulk-applied without current-head remapping and tests.

## Exit criteria for this audit lane

This lane is complete when the audit artifacts exist on a PR and the project has a durable record that:

- admissions advanced workflow is not certified
- dashboards are mapped only
- wizards are contract-only
- PROVEN modules require proof-depth recheck
- NOT_PROVEN modules remain open until current-head evidence is merged
- no release or production claim is made
