# CROWN Same-SHA Live Sandbox Role-Path Proof (#1220)

Date: 2026-07-02
Issue: #1220 (Prepare same-SHA live sandbox and role-path proof plan)
Scope hygiene note: Reissued as docs-only packet from current main to isolate release evidence updates from non-doc changes.

## Status

Same-SHA live runtime proof has been captured and reviewed.

Result: FAIL.

This evidence does not support sandbox launch approval or production approval.

## Scope

- Record same-SHA run metadata.
- Record role and tenant coverage attempted by the live crawler.
- Record binary outcome and blockers.

## Non-Scope

- No release approval.
- No closure of #1220.
- No closure of #1219.

## Evidence metadata

```text
main_sha: 402c4e7a0cee7c771c82d5ec0954273219a2346e
workflow_name: Production Certification Evidence
workflow_run_id: 28574455949
workflow_run_url: https://github.com/tcmegahan/Crown2026/actions/runs/28574455949
workflow_run_event: workflow_dispatch
workflow_run_branch: main
workflow_run_conclusion: failure
artifact_id: 8032405394
artifact_name: production-certification-evidence-9-402c4e7a0cee7c771c82d5ec0954273219a2346e
```

## Coverage attempted

Roles/personas attempted:

- admin
- teacher
- parent
- student
- board

Tenants attempted:

- heritage
- harvest
- faith

Expected evidence files present:

- certification-summary.md
- certification-matrix.json
- route-results.csv
- failed-requests.json
- console-errors.json
- accessibility-violations.json
- screenshots/

## Outcome summary

- Total checks: 33
- Passed: 0
- Failed: 33
- Certification summary status: FAIL

Primary failure patterns:

1. Token auth failures on prod host for most role/tenant paths:
   - POST https://crown-api-prod.azurewebsites.net/api/v1/auth/token/ -> 401
2. Board path failure:
   - live login role option not found for role board
3. Host consistency anomaly (heritage admin path):
   - POST https://crown-api-dev.azurewebsites.net/api/v1/auth/token/ -> net::ERR_FAILED
   - CORS block observed

Accessibility result from artifact file:

- critical/serious accessibility violations: 0

## Decision

Binary disposition for #1220 evidence lane: FAIL (proof captured, not passing).

#1220 remains OPEN.

## Exit criteria to close #1220

1. Re-run same workflow on a new main SHA after auth credentials/role path/host consistency blockers are corrected.
2. Obtain passing role-path evidence for admin, teacher, parent, student, and board across heritage, harvest, and faith.
3. Ensure no failed API requests, no blocking console errors, and expected API calls observed.
4. Link the passing run and artifact metadata in this document and in `docs/release/CROWN_RELEASE_EVIDENCE_INDEX.md`.
