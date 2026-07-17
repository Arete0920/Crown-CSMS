# Schema Recovery Evidence Procedure

Status: NON-PRODUCTION EVIDENCE LANE

Related: #1387, #1270, #1275, #1374

## Purpose

Prove that CROWN's controlled migration authority can recover safely from lock contention, an interrupted lock-holder session, and a partially rolled-back schema without using production data or allowing ordinary web startup to mutate schema.

## Safety boundary

- The first recovery ceremony runs only against the disposable PostgreSQL service created inside GitHub Actions.
- No production database URL, Azure environment, production secret, customer data, or tenant data is used.
- The workflow does not deploy an application or alter production release authority.
- The workflow records the exact Git commit SHA and GitHub Actions run ID.
- Production remains not approved until all controlling release blockers are reconciled.

## Evidence workflow

Workflow: `.github/workflows/schema-recovery-evidence.yml`

The workflow performs these cases in order:

1. **Clean database** — execute all migrations through `migrate_with_lock` using a real PostgreSQL advisory lock.
2. **Current database** — repeat the command and run lock-protected check mode to prove idempotency.
3. **Concurrent invocation** — hold advisory lock `2026071701` in a separate PostgreSQL session and prove a second migration command times out and fails closed.
4. **Interrupted authority** — terminate the lock-holder client and prove PostgreSQL releases the session advisory lock so a new migration authority can proceed.
5. **Partially rolled-back schema** — roll the disposable database back to `contenttypes 0001` and prove `migrate --check` rejects the stale schema.
6. **Failed readiness blocks web/deploy continuation** — treat the nonzero schema check as a hard stop; no readiness success is recorded while the schema is stale.
7. **Forward-fix rehearsal** — execute `migrate_with_lock` again and prove the database returns to a current migration state.
8. **Web non-mutation** — run the source contract proving production startup scripts use `migrate --check` and deployment waits for the controlled migration stage.

## Required result

A passing run must produce a timestamped artifact named:

`schema-recovery-evidence-<exact-commit-sha>`

The artifact contains:

- advisory-lock holder output;
- failed contention attempt output;
- stale-schema check output;
- recovered migration plan.

## Failure handling

- Do not rerun blindly.
- Inspect the first failed step and its uploaded evidence.
- Classify the failure as workflow defect, application migration defect, PostgreSQL behavior mismatch, or runner/infrastructure failure.
- Correct only the demonstrated cause on the same evidence branch.
- Re-run once after the correction and preserve both run references in #1387.

## Closure rule for #1387

Do not close #1387 from source wiring alone. Closure requires:

- this disposable PostgreSQL recovery workflow passing on an exact SHA;
- artifact and run links recorded in #1387;
- the merged production deployment source still ordering exact-SHA migration before web deployment;
- ordinary startup still containing no schema mutation command;
- explicit linkage to #1270, #1275, and #1374;
- no claim that this evidence independently authorizes production.
