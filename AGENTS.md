# CROWN Repository Work Contract

This contract applies to contributors, automation, development tools, and support processes working in this repository.

## Role and authority

Repository tools and automation may inspect files, execute explicitly scoped work, run validation, create evidence, and summarize risk. They do not own product requirements, architecture decisions, acceptance, security approval, or release authority.

No contributor, tool, or automated process may self-approve work, declare release readiness, declare production readiness, bypass governance, broaden scope without authorization, or treat local passing tests as independent review.

## Current product name

Public-facing product name: CROWN  
Descriptor: Christian School Management Solution

Avoid public-facing `Crown2026` branding except where repository, branch, artifact, or historical filenames require it.

## Required first step

Before making changes, identify:

```text
BRANCH=<current branch>
HEAD=<current sha>
TASK=<one sentence>
EXPECTED_FILES=<exact paths or directories>
FORBIDDEN_FILES=<exact paths or directories>
VALIDATION=<commands to prove the work>
```

If expected files cannot be named, do not edit.

## Source of truth

Use current repository evidence over memory, copied notes, or stale status material.

For module status, read:

- `audit-artifacts/module-completion/current/01_module_matrix_expanded.csv`
- `audit-artifacts/module-completion/current/05_completion_scorecard.md`

For wizard status, read:

- `docs/release/WIZARD_EVIDENCE_BOUNDARY_20260614.md`
- current wizard certification matrix files

For dashboards, read the current dashboard certification matrix and dashboard registry.

## Evidence rules

Every completion claim requires proof from at least one of:

- committed file path and line or section;
- raw command output;
- generated audit artifact;
- automated test result;
- GitHub pull request number and head SHA;
- CI check result.

If proof is missing, state `NOT VERIFIED`.

## Forbidden claims without explicit proof

Do not write or imply these unless the specific claim is proven by current evidence:

- forbidden claim: production ready
- forbidden claim: release ready
- forbidden claim: sandbox ready
- forbidden claim: dashboard live-data complete
- forbidden claim: wizard functional-flow complete
- forbidden claim: all wizards complete
- forbidden claim: all modules complete
- forbidden claim: independently approved
- forbidden claim: fully certified
- complete platform

## Scope rules

Use isolated branches and worktrees. Do not mutate `main` directly.

Use separate pull requests for:

1. proof implementation;
2. canonical scorecard or matrix reconciliation;
3. governance or process documentation;
4. workflow or CI changes;
5. release certification.

Do not mix implementation and scorecard reconciliation unless explicitly authorized.

## Protected areas

Do not change these without explicit scope:

- authentication;
- RBAC;
- tenant or school isolation;
- database migrations;
- production deployment;
- GitHub workflows;
- Azure resources;
- secrets;
- package manifests and lock files;
- repository rulesets or branch protections.

## Review rule

The repository owner cannot approve their own work. A contributor or automated process cannot independently approve work it produced. Use `INDEPENDENT_REVIEW_REQUIRED` unless an appropriate independent reviewer has completed review.

## Required closeout format

Every task report must include:

- Status;
- Evidence found;
- Files changed;
- Validation run;
- Risks;
- Next exact command.
