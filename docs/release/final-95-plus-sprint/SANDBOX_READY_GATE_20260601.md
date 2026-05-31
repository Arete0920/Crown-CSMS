# CROWN Sandbox Ready Gate - Target 2026-06-01

Status: ACTIVE SANDBOX-READINESS GATE
Authority: Non-shipping control artifact until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Purpose

This gate defines the minimum evidence required before CROWN can be called sandbox-ready. Calendar target alone is not sufficient.

## Decision states

| Decision | Meaning |
|---|---|
| SANDBOX GO | All sandbox-critical gates pass and limitations are explicit |
| SANDBOX CONDITIONAL | Core sandbox works, but noncritical limitations remain documented |
| SANDBOX NO-GO | Any sandbox-critical gate fails or is missing proof |

## Sandbox GO criteria

| Gate | Required result | Current status |
|---|---|---|
| Repo truth freeze | PASS | NOT VERIFIED |
| Backend Django check | PASS | NOT VERIFIED |
| Migration dry-run | PASS | NOT VERIFIED |
| Seed/demo reset path | PASS | NOT VERIFIED |
| Sandbox login path | PASS | NOT VERIFIED |
| Sandbox school selection or routing | PASS | NOT VERIFIED |
| Critical frontend build | PASS | NOT VERIFIED |
| Route/navigation smoke | PASS | NOT VERIFIED |
| Tenant isolation smoke | PASS | NOT VERIFIED |
| Public admissions start/apply path | PASS | NOT VERIFIED |
| Parent sandbox journey smoke | PASS | NOT VERIFIED |
| Teacher sandbox journey smoke | PASS | NOT VERIFIED |
| Admin sandbox journey smoke | PASS | NOT VERIFIED |
| Billing/aid visible-state smoke | PASS or explicitly hidden | NOT VERIFIED |
| Dashboard release-state truth | PASS | NOT VERIFIED |
| Known sandbox limitations | Explicit and visible | NOT DONE |

## Sandbox-specific integrity rules

1. Sandbox must not be represented as production.
2. Sandbox demo data must be clearly non-production.
3. Sandbox login options must be appropriate to sandbox context.
4. Sandbox routes must not expose unguarded sensitive production paths.
5. Sandbox dashboards may show sample/demo data only if clearly labeled.
6. Any unavailable module must be hidden or honestly marked unavailable.

## Required evidence artifacts

- `FINAL_SANDBOX_READY_PACKET.md`
- `FINAL_SANDBOX_LOGIN_PROOF.md`
- `FINAL_SANDBOX_ROUTE_NAVIGATION_PROOF.md`
- `FINAL_SANDBOX_DEMO_DATA_POLICY.md`
- `FINAL_SANDBOX_LIMITATIONS.md`

## Required local proof

Run the baseline evidence pack first:

`docs/release/final-95-plus-sprint/VSCODE_SINGLE_BLOCK_EVIDENCE_RUN_20260530.md`

Then run sandbox-specific smoke tests if available:

```powershell
Push-Location frontend\dashboards
npm run ui:proof:sandbox
Pop-Location
```

If that script is unavailable or fails, capture the output and classify sandbox readiness as `SANDBOX NO-GO` until fixed.

## Current decision

SANDBOX NO-GO until current evidence is generated and reviewed.
