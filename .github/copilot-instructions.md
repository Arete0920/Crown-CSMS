# CROWN Copilot / VS Code Guardrails

## Absolute Operating Rule

Do not guess, assume, invent, infer, or fill in missing CROWN implementation details.

If evidence is missing, stop and report:
- what is missing;
- where you searched;
- what cannot be proven;
- what exact file or command is needed next.

## Role Boundary

Copilot and AI assistants are support, not deciders.

They may:
- inspect files;
- draft bounded work orders;
- implement explicitly scoped fixes;
- run local tests;
- generate evidence packets;
- summarize risk.

They may not:
- approve their own work;
- declare production readiness;
- declare release readiness;
- bypass branch policy;
- treat local passing tests as independent review;
- broaden scope without an explicit work order.

## Active CROWN Workstreams

Current high-priority workstreams are:

1. Module proof closure for the remaining NOT_PROVEN modules.
2. Canonical matrix and scorecard reconciliation after proof is merged.
3. Wizard functional-flow certification beyond route/API contract coverage.
4. Dashboard live-data validation beyond mapped route coverage.
5. Release-readiness evidence only after module, wizard, dashboard, security, runtime, and independent-review gates are complete.

Do not use stale workstream labels as authority. Read the current canonical files first:
- `audit-artifacts/module-completion/current/01_module_matrix_expanded.csv`
- `audit-artifacts/module-completion/current/05_completion_scorecard.md`
- `docs/release/WIZARD_EVIDENCE_BOUNDARY_20260614.md`
- `docs/release/WIZARD_CERTIFICATION_MATRIX_20260530.md`
- `docs/release/DASHBOARD_CERTIFICATION_MATRIX_20260530.md`

## No-Wandering Rule

Before changing any file, produce:
1. current branch;
2. current HEAD;
3. exact task;
4. files expected to change;
5. files explicitly not allowed to change;
6. validation commands that will prove the work.

If you cannot name the files expected to change, do not edit.

## No-Breakage Rule

Never perform broad refactors, mass renames, formatting-only rewrites, dependency upgrades, migration changes, route rewires, auth changes, tenant changes, Azure changes, GitHub workflow changes, package changes, or deletion unless the user explicitly asks for that exact action.

## Protected Areas

Do not change these unless explicitly authorized:
- authentication;
- RBAC;
- tenant/school isolation;
- database migrations;
- production deployment;
- Azure resources;
- GitHub repository settings;
- branch/ruleset configuration;
- secrets;
- package manifests;
- lock files;
- existing working tests unrelated to the task.

## Evidence Rule

Every claim must be backed by at least one of:
- file path and line or section;
- command output;
- generated audit artifact;
- test result;
- git diff;
- PR number and head SHA.

When evidence is not current, say NOT VERIFIED.

## Module Done Definition

A module is PROVEN only when the canonical proof requirement for that module is satisfied with committed evidence and passing validation.

At minimum, a module proof lane must establish:
1. exact current blocker from the canonical matrix;
2. implementation files, or evidence that implementation is missing;
3. automated tests for the blocker;
4. tenant/school isolation where data is scoped;
5. role/permission behavior where API access exists;
6. evidence packet with raw command output;
7. no unrelated file changes;
8. PR body with bounded claims only.

A separate canonical reconciliation PR should update scorecard/matrix after proof PRs merge.

## Wizard Done Definition

A wizard is not done because a screen exists.

A wizard is PASS only when it has:
1. central registry/manifest entry;
2. route/navigation wiring;
3. frontend wizard flow;
4. API/service contract;
5. model/schema/entity contract where data persists;
6. role/permission enforcement;
7. tenant/school isolation;
8. KPI/metric wiring;
9. seed/demo/sandbox data;
10. automated tests/proof;
11. documentation/canon entry;
12. audit/logging/event trail where required.

Anything less is REVIEW, FAIL_PARTIAL, or FAIL_MISSING.

## Dashboard Done Definition

A dashboard is not live because it is registered or mapped.

A dashboard is LIVE only when it has:
1. route registration;
2. rendered UI proof;
3. authenticated API/data source wiring;
4. tenant-scoped data behavior;
5. loading/empty/error states;
6. role visibility behavior;
7. automated or captured runtime evidence;
8. no mock-only data in the certified path.

## Required Response Format For Work

Use this structure:
- Status
- Evidence found
- Files changed
- Validation run
- Risks
- Next exact command

Do not use vague language such as should, probably, likely fixed, seems fine, essentially done, or production ready unless the claim is explicitly proven.

## Accounting Copilot Safety Rules

1. NEVER MODIFY LEDGER IMMUTABILITY.
2. NEVER USE FLOAT TYPES.
3. NEVER STORE DERIVED BALANCES AS SOURCE OF TRUTH.
4. NEVER CREATE SINGLE-ENTRY ACCOUNTING.
5. NEVER GENERATE MOCK ACCOUNTING LOGIC.
6. NEVER BYPASS VALIDATION SERVICES.
7. NEVER CREATE CROSS-TENANT QUERIES.
8. NEVER REMOVE AUDIT LOGGING.
9. NEVER AUTO-GENERATE MIGRATIONS WITHOUT REVIEW.
10. NEVER USE DELETE OPERATIONS ON LEDGER DATA.
11. ALL ACCOUNTING CODE MUST INCLUDE TESTS.
12. ALL ACCOUNTING CHANGES REQUIRE reconciliation verification, integrity verification, and tenant isolation verification.

## Branch And PR Rule

Use isolated branches and worktrees. Do not mutate `main` directly.

Every PR must state:
- exact scope;
- exact non-scope;
- files changed;
- validation commands;
- evidence artifacts;
- current head SHA;
- whether independent review is still required.
