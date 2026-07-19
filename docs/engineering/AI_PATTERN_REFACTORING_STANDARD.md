# AI-Pattern Refactoring Standard

**Status:** Canonical engineering standard  
**Owner:** TC Megahan, Founder/Product Owner  
**Related program:** #1432

## Purpose

This standard defines how CROWN identifies and remediates code and repository patterns commonly associated with rushed, copied, generated, or weakly reviewed development.

The term **AI pattern** describes a quality, verification, or provenance risk. It does not establish authorship.

## Governing principles

1. Preserve behavior unless an approved issue explicitly authorizes a behavior change.
2. Use current repository evidence rather than assumptions.
3. Refactor in bounded subsystem-specific pull requests.
4. Separate implementation refactors, governance documentation, CI changes, and release certification.
5. Do not change authentication, RBAC, tenant isolation, migrations, deployment, workflows, secrets, package manifests, or repository controls without explicit scope.
6. Search active references and replacement paths before deleting or renaming code.
7. Mark unsupported conclusions `NOT VERIFIED`.
8. Do not use automated findings as proof of AI authorship.

## Finding classes

### AP-01: Temporary, urgency, or outcome-claiming names

Examples: `tmp`, `temporary`, `finish_now`, `final_final`, `autopilot`, `magic`, `one_click`, `gauntlet`, `fix_everything`, or `complete` when used as an unsupported outcome claim.

Risk: unclear purpose, stale one-off automation, duplicate workflows, and false authority.

Remediation: rename around the exact operation, inputs, outputs, and scope. Delete only after reference and replacement analysis.

### AP-02: Machine-specific paths or environment assumptions

Examples: hard-coded user directories, drive letters, workstation names, local repository paths, fixed ports, or timestamped artifact locations.

Risk: non-reproducible execution and hidden environmental coupling.

Remediation: resolve the repository root, accept parameters, use documented environment variables, and fail with an actionable message.

### AP-03: Embedded verdicts or synthetic status

Examples: literal `PASS`, `SAFE`, `Keep`, `Partial`, `Current`, `production-ready`, or completion classifications that are not calculated from current evidence.

Risk: fabricated confidence and stale release, maturity, security, or completion claims.

Remediation: derive status from explicit rules and current inputs. Otherwise emit `NOT ASSESSED` or `NOT VERIFIED`.

### AP-04: Broad exception handling

Examples: broad catches that continue silently, return success, discard context, or suppress required failures.

Risk: hidden defects and misleading evidence.

Remediation: catch the narrowest exception, retain context, return a non-zero result for required failed work, and test the failure path.

### AP-05: Mixed-responsibility scripts or modules

Examples: one script performs cleanup, environment mutation, repository inspection, tests, governance checks, deployment checks, and release verdicts.

Risk: high blast radius, poor testability, unclear rollback, and accidental authority escalation.

Remediation: separate discovery, validation, mutation, reporting, and release authority into focused commands.

### AP-06: Narrative comments and redundant documentation

Examples: comments that restate the next line, large separator banners, copied chat narrative, repeated historical summaries, or multiple documents claiming current authority.

Risk: maintenance noise, contradiction, and buyer-facing confusion.

Remediation: retain comments that explain constraints or non-obvious decisions. Remove narration and point to one canonical authority source.

### AP-07: Placeholder or sample behavior in runtime paths

Examples: hard-coded sample responses, fabricated metrics, placeholder success objects, unimplemented branches returning plausible data, or fail-open defaults.

Risk: false functional proof and unsafe production behavior.

Remediation: fail closed, isolate demo fixtures, add explicit configuration gates, and test enabled and disabled behavior.

### AP-08: Duplicated wrappers and speculative abstraction

Examples: multiple HTTP clients, repeated adapters, nearly identical scripts, generic helper layers with one caller, or configuration aliases with unclear precedence.

Risk: inconsistent behavior and unnecessary indirection.

Remediation: select one canonical implementation, migrate callers, add contract tests, and remove the orphan only after reference analysis.

### AP-09: Oversized files and functions

Review triggers include functions with unrelated operations, modules that mix transport, domain logic, persistence, formatting, and orchestration, or scripts that cannot be validated without executing the entire workflow.

Size alone is not a defect.

Remediation: extract around stable responsibilities and preserve the public contract with tests.

### AP-10: Generated or copied repository debris

Examples: timestamped proof dumps, local logs, temporary command files, copied chat output, redundant reports, generated source without an authority purpose, or stale historical evidence in active paths.

Risk: repository noise, secret leakage, stale claims, and diligence confusion.

Remediation: delete, archive, or relocate according to evidence-retention rules; add ignore or generation controls where appropriate.

### AP-11: Unproven attribution or authorship claims

Risk: inaccurate contributor history and diligence exposure.

Remediation: use the Contribution Evidence Ledger and mark unsupported claims `NOT VERIFIED`.

### AP-12: Repetitive boilerplate and shallow abstraction

Examples: repeated near-identical CRUD blocks, generic comments, copy-pasted validation, duplicated constants, or helpers that merely rename one operation.

Risk: drift, inconsistent fixes, and increased review cost.

Remediation: consolidate only when behavior and ownership boundaries are stable. Avoid speculative frameworks.

### AP-13: Unbounded or non-diagnostic automation

Examples: deep scans without timeouts, long runners without progress evidence, or failed jobs that do not retain logs.

Risk: indefinite CI, unverifiable failures, and blocked release queues.

Remediation: bound execution, retain diagnostics with `if: always()`, and fail closed for required work.

## Severity

- **Critical:** security, privacy, tenant isolation, release authority, secret exposure, or destructive-data risk.
- **High:** executable stale automation, false verdicts, hard-coded environment coupling, fulfillment or authorization bypasses, or behavior that can materially mislead validation.
- **Medium:** duplication, broad exception handling, excessive complexity, weak testability, or non-critical placeholder behavior.
- **Low:** naming, narration, formatting, decorative separators, or localized maintainability noise.

Severity reflects impact and evidence, not how strongly a pattern resembles generated code.

## Required refactor record

Each refactor pull request must state:

```text
Finding IDs:
Human owner:
Evidence-backed contributors:
AI assistance:
Baseline behavior:
Files changed:
Behavior intentionally changed:
Validation:
Rollback:
Remaining NOT VERIFIED items:
```

## Verification sequence

1. Confirm the current base, branch, and exact head SHA.
2. Confirm the bounded issue and permitted files.
3. Search active references before deletion or rename.
4. Capture baseline behavior and focused tests.
5. Apply the smallest coherent refactor.
6. Run focused tests and relevant broader contracts.
7. Review the final diff for unrelated changes.
8. Record exact-head CI evidence.
9. Resolve or explicitly disposition actionable review findings.
10. Merge with head-SHA locking under the applicable governance control.
11. Verify post-merge behavior where the change affects runtime or control-plane behavior.

## Initial repository candidates

The following remain candidates for bounded review based on issue #1432 and prior repository inspection:

- `scripts/execution/_tmp_triage.cmd` — machine-specific path, fixed historical artifacts, embedded verdicts, and no active source reference previously found;
- `scripts/crown_finish_now.ps1` — mixed cleanup, governance, testing, GitHub, and release-closeout responsibilities;
- `scripts/execution/110_deep_audit_autopilot.ps1` — synthetic classifications and shallow text-derived maturity claims;
- `scripts/execution/999_finish_right_4h_gauntlet.ps1` — broad validation orchestration and release-adjacent verdict language.

Candidate status does not authorize deletion. Each file requires current reference analysis, replacement analysis, and scoped validation.