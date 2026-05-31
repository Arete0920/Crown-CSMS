# CROWN Final 95+ First-Failure Triage Runbook - 2026-05-30

Status: ACTIVE FINAL-SPRINT TRIAGE RUNBOOK
Authority: Non-shipping operational runbook until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Purpose

The final sprint must move fast without creating more noise. The operating method is first-failure isolation: run the evidence pack, stop at the first failing gate, fix only that failure, then re-run focused proof.

Do not stack speculative fixes. Do not update release authority based on incomplete runs. Do not broaden scope while an earlier gate is red.

## Triage order

### Phase 1 - Repo truth

If repo truth freeze fails:

1. Confirm branch is `main` or approved release branch.
2. Confirm `git pull` completed.
3. Confirm working tree status.
4. Do not proceed with scoring until repo state is clean or explicitly documented.

### Phase 2 - Backend bootstrap

If Python/Django check fails:

1. Capture full output.
2. Identify first stack trace or first system check error.
3. Fix only that error.
4. Re-run `python backend/manage.py check`.
5. Do not run broader suites until check passes.

### Phase 3 - Migrations

If migration dry run fails:

1. Determine whether model changes require migration.
2. Generate migration only for intended model change.
3. Do not fabricate empty merge migrations unless graph drift requires it.
4. Re-run `makemigrations --check --dry-run`.

### Phase 4 - Deploy check

If deploy check fails:

1. Distinguish expected local warnings from real production blockers.
2. Production blockers must be fixed or documented as NO-GO.
3. Do not suppress warnings without clear reason.

### Phase 5 - Tenant/RBAC/backend tests

If tenant/RBAC/backend test fails:

1. Identify the first failing test.
2. Read the test expectation before editing code.
3. Determine whether the code or test is wrong.
4. Fix only the narrow contract mismatch.
5. Add/adjust regression proof if the issue exposes a missing case.

### Phase 6 - Frontend install/lint/contracts

If `npm ci` fails:

1. Do not edit application code.
2. Resolve dependency/lockfile issue first.

If lint fails:

1. Fix only lint-reported files.
2. Avoid behavior changes unless required.

If contracts fail:

1. Read contract expectation.
2. Fix route/API/nav/role definition or test expectation based on canonical contract.

### Phase 7 - Shell certification/readiness

If shell certification fails:

1. Identify fake-ready route, missing readiness flag, missing owner/module metadata, placeholder signal, duplicate key, or invalid path.
2. If a route is not complete, mark it non-ready rather than pretending it is ready.
3. If a route is complete, add missing metadata and proof.

### Phase 8 - Build

If build fails:

1. Capture first compiler/bundler error.
2. Fix only import/export/type/path issue causing the build failure.
3. Re-run build.

### Phase 9 - Release scripts

If API contract/navigation/release verification fails:

1. Treat the script output as authoritative for the target contract.
2. Do not bypass release scripts.
3. Fix the route/API/nav source of truth or update the verifier only if the verifier is demonstrably stale.

## Evidence capture requirement

Every failure and fix cycle must produce:

- failing command output,
- file(s) changed,
- reason for change,
- focused re-run output,
- updated status.

## Commit discipline

Preferred commit shape:

1. One commit for evidence capture.
2. One narrow commit for first-failure fix.
3. One commit for focused proof after fix.

Do not combine broad unrelated fixes into a single commit.

## Status language

Allowed:

- `Gate failed: first blocker isolated.`
- `Focused fix applied.`
- `Focused proof passed.`
- `Gate remains NOT DONE.`

Forbidden:

- `Basically done.`
- `Should pass.`
- `Probably fixed.`
- `Good enough.`
- `We can clean this up later.`

## Release authority rule

Never update `docs/CURRENT_RELEASE_STATUS.md` to unrestricted GO until:

1. All P0 local evidence is green.
2. Deploy SHA parity is green.
3. Protected-spine packet is green.
4. Policy gate packet is green.
5. Final scorecard has every required area at 95+.
6. Compliance/customer readiness packet is complete.

## Current runbook conclusion

Use this runbook immediately after the VS Code command pack produces evidence. First failure controls the next action.
