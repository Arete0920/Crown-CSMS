# CROWN CI Proof Ownership Ledger

Status: execution inventory under #1394  
Goal: one explicit proof hierarchy with no unowned, contradictory, or silently duplicated release claims

## Proof levels

1. **Static contract** — source shape, configuration, route, schema, dependency, or policy assertions.
2. **Focused component** — bounded backend or frontend tests for one changed domain.
3. **Integrated application** — backend/frontend build, API contract, tenant, accounting, and cross-module behavior.
4. **Sandbox runtime** — authenticated browser and API behavior against controlled sandbox data.
5. **Release-candidate authority** — exact frontend/backend SHA binding, immutable evidence, rollback target, and all required gates.
6. **Production ceremony** — controlled schema stage, deployment, runtime provenance, health, tenant integrity, and recovery evidence.

No workflow may use readiness terminology without identifying its proof level and explicit non-claims.

## Workflow classification fields

Every active workflow must be recorded with:

- file and display name;
- triggers and path filters;
- required or advisory status;
- branch-protection context;
- jobs and major commands;
- duplicated commands also run elsewhere;
- expected artifacts and retention;
- timeout, cancellation, concurrency, and retry behavior;
- secrets and environment dependencies;
- proof level and exact supported claim;
- unsupported claims;
- owning issue/runbook;
- retirement or consolidation disposition.

## Target ownership model

| Category | Purpose | Execution expectation |
| --- | --- | --- |
| Merge gate | blocks unsafe source integration | fast, deterministic, changed-domain aware where safe |
| Release gate | validates exact candidate SHA and complete release contract | broad, fail closed, immutable evidence |
| Scheduled assurance | detects drift and latent failures | non-merge-blocking unless promoted through a defect issue |
| Evidence generator | produces proof artifacts without independently authorizing release | artifact-focused and provenance-bound |
| Advisory diagnostic | expands failure context | never mistaken for approval |
| Obsolete/duplicate | no unique proof ownership | removed only after equivalence evidence |

## Initial duplicate-execution clusters

The active repository currently has overlapping broad checks including general tests, CI tests and checks, pytest gate, backend gate, contract gate, release verify, proof ceremonies, release authority gates, sandbox evidence, and phase gates. Similar names do not establish equivalence; each must be mapped to its exact commands and outputs before consolidation.

Priority analysis clusters:

1. Python test repetition across Tests, CI Tests and Checks, pytest-gate, backend-gate, and domain gates.
2. Frontend build and route repetition across dashboard build, UI proof, route, sandbox, and proof ceremonies.
3. Release terminology overlap across Release Verify, Release Scorecard, RC promotion, Release Authority, Proof Ceremony, and Phase 3 Runtime Proof Ceremony.
4. Dependency and security overlap across Dependency Review, Dependency Audit, Dependency Scan, secret scan, CodeQL, and public repository quality checks.
5. Canon and claims overlap across Spine Audit, Claims Guard, PR Hygiene, and release documentation checks.

## Consolidation rules

- Do not remove a required check before branch-protection inventory and equivalence proof.
- Do not use path filtering for security, schema, tenant, accounting, dependency, or release-authority checks unless the unaffected-path argument is proven.
- Prefer reusable workflows or shared scripts over copied command blocks.
- Preserve unique check names during staged migration when branch protection depends on them.
- Separate diagnostic artifact generation from the binary gate decision where possible.
- Failures must identify the responsible proof domain and exact failing command.
- Repeated identical failures trigger root-cause review rather than blind reruns.
- Release authority must bind the same immutable source, frontend artifact, backend artifact, schema stage, and deployed runtime provenance.

## Measurement baseline

Before consolidation, capture for at least twenty representative PR runs:

- total wall-clock duration;
- runner minutes;
- queue time;
- repeated command count;
- repeated dependency-install count;
- flaky or rerun count;
- first-failure localization time;
- artifact volume;
- checks required by branch protection.

After each consolidation group, compare the same measures while proving no material assurance was lost.

## Ordered work packages

1. Complete active workflow and branch-protection inventory.
2. Build command-level duplicate matrix.
3. Normalize proof-level terminology and non-claims.
4. Extract repeated setup and test commands into shared scripts or reusable workflows.
5. Consolidate one low-risk duplicate cluster at a time.
6. Preserve compatibility check contexts during transition.
7. Establish one exact-SHA release-candidate ceremony.
8. Bind schema migration, deployment, runtime provenance, rollback, and recovery into the production ceremony.
9. Retire obsolete workflows and update canonical documentation.

## Closure rule

Issue #1394 closes only when every active workflow has unique documented ownership, branch protection references intentional checks, duplicate execution is eliminated or justified, proof levels are non-contradictory, failure localization is explicit, and one same-SHA authority ceremony governs final release evidence.
