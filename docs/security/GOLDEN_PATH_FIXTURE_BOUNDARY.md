# Golden Path seed boundary

The Golden Path bootstrap is a DEV or isolated-local proof command, not a
customer onboarding tool or an administrator recovery operation.

## Safeguards

- In hosted DEV, supply an explicit school UUID. An existing school must match
  the named canonical demo-school identity `Crown Demo School`.
- In local SQLite without a UUID, the command uses only `GP School` and never
  selects the database's first school.
- Production environment labels and non-DEV hosting contexts are rejected.
- The legacy demonstration administrator username may not be reassigned from a
  different tenant, and an existing non-administrator may not be elevated.
  Administrator credential provision remains governed separately.
- `--force` does not erase existing admissions applications or events. If
  applicants already exist, the admissions funnel is preserved and reported
  as skipped. Rebuilds requiring removal must use an approved isolated reset.
- Fresh fixtures use 94 plausible fictional applicant names, with stable
  independent household identifiers and a reproducible stage distribution.
  These are synthetic scenarios, not lead contacts or evidence of conversion.
- Golden Path financial-aid fixture IDs are UUIDv5 values derived from the
  canonical school UUID and a named fixture key, eliminating cross-school
  reuse of global sequential IDs. Existing legacy IDs are not deleted or
  silently migrated.
- Historical migrations and production API schema fields remain unchanged.

## Test contract

Run `pytest backend/core/tests/test_golden_path_fixture_safety.py
backend/tests/test_golden_path_bootstrap_school_create.py` and all governed
repository CI checks before acceptance.

This correction does not establish deployed DEV operation or authorize
production use.
