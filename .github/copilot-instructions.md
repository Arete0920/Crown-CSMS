# Crown Copilot / VS Code Guardrails

## Absolute Operating Rule

Do not guess, assume, invent, infer, or "fill in" missing Crown implementation details.

If evidence is missing, stop and report:
- what is missing
- where you searched
- what cannot be proven
- what exact file or command is needed next

## Current Workstream

The active workstream is the 50 Wizard Deep Dive.

The valid scope is:
- 50 parent wizard rows
- function
- operation
- KPI
- registry
- route/navigation
- frontend wizard flow
- API/service contract
- model/schema/entity contract
- permissions/RBAC
- tenant/school isolation
- seed/demo/sandbox data
- tests/proof
- docs/canon entry
- audit/logging trail
- fix queue

## No-Wandering Rule

Before changing any file, produce:
1. current branch
2. current HEAD
3. exact task
4. files expected to change
5. files explicitly not allowed to change
6. validation commands that will prove the work

If you cannot name the files expected to change, do not edit.

## No-Breakage Rule

Never perform broad refactors, mass renames, formatting-only rewrites, dependency upgrades, migration changes, route rewires, auth changes, tenant changes, Azure changes, GitHub workflow changes, package changes, or deletion unless the user explicitly asks for that exact action.

## Protected Areas

Do not change these unless explicitly authorized:
- authentication
- RBAC
- tenant/school isolation
- database migrations
- production deployment
- Azure resources
- GitHub repository settings
- branch/ruleset configuration
- secrets
- package manifests
- lock files
- existing working tests unrelated to the task

## Evidence Rule

Every claim must be backed by:
- file path
- line/section or command output
- generated audit artifact
- test result
- git diff

## Wizard Done Definition

A wizard is not done because a screen exists.

A wizard is PASS only when it has:
1. central registry/manifest entry
2. route/navigation wiring
3. frontend wizard flow
4. API/service contract
5. model/schema/entity contract where data persists
6. role/permission enforcement
7. tenant/school isolation
8. KPI/metric wiring
9. seed/demo/sandbox data
10. automated tests/proof
11. documentation/canon entry
12. audit/logging/event trail where required

Anything less is REVIEW, FAIL_PARTIAL, or FAIL_MISSING.

## Response Format For Work

Use this structure:
- Status
- Evidence found
- Files changed
- Validation run
- Risks
- Next exact command

Do not use vague language such as "should", "probably", "likely fixed", or "seems fine" when reporting completion.

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

12. ALL ACCOUNTING CHANGES REQUIRE:
	- reconciliation verification
	- integrity verification
	- tenant isolation verification
