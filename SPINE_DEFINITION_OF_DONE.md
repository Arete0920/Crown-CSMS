# SPINE — DEFINITION OF DONE (NON-NEGOTIABLE)

Spine work is considered DONE only when ALL items below are true.

## Determinism
- Demo users can be reset to a known state via ONE command.
- No passwords are guessed or remembered.
- All critical state is recoverable without SSH exploration.

## Auth & Tenancy
- Authenticated request without X-School-Id fails deterministically.
- Authenticated request with wrong X-School-Id fails deterministically.
- Authenticated request with correct X-School-Id succeeds.

## Environment Clarity
- CROWN_ENV explicitly set in DEV and PROD.
- PROD behavior differs only where documented.
- Content negotiation rules are verified by probe.

## Recovery
- A documented command exists to recover from:
  - auth drift
  - demo data drift
  - tenant confusion

## Evidence Required
- Commands executed
- Status lines / top-level keys captured
- Tests passing
- Commit SHA recorded

If any item above is false, the spine is NOT DONE.
No feature work may proceed.
