# Wizard contract vs runtime boundary reset

Date: 2026-06-16
Scope: audit only

## Current credited status

The current scorecard credits 28 of 28 wizards as FLOW_CONTRACT_VALIDATED.

## Boundary

FLOW_CONTRACT_VALIDATED means the wizard has route/API contract inventory coverage. It does not certify:

- full end-to-end functional wizard completion
- real browser runtime walkthroughs
- complete form validation behavior
- persistence and reload behavior
- role-by-role access walkthroughs
- visual QA
- production readiness
- independent release approval

## Required certification upgrade

A wizard may move from FLOW_CONTRACT_VALIDATED to FUNCTIONAL_FLOW_CERTIFIED only when the evidence packet proves:

1. Route loads in browser for the intended role.
2. User can complete the wizard happy path.
3. User can save/commit/submit as applicable.
4. Backend state changes are verified through API/database evidence.
5. Validation/error paths are checked.
6. Tenant and role boundaries are checked.
7. Evidence includes screenshots or runtime trace plus API response evidence.
8. Evidence cites current commit SHA.

## Impact of admissions finding

The admissions false-completion finding proves that route/API or planning artifacts can mask missing workflow implementation. Therefore no wizard should be treated as production-ready based only on route/API contract coverage.

## Status

Wizard release status: NOT RELEASE-CERTIFIED
Wizard current valid claim: 28/28 route/API contract coverage only
Required next work: full functional-flow certification lane
