# CROWN Agent Operating Contract

This file applies to all AI assistants, coding agents, ChatGPT/Copilot sessions, and automated support tools working in this repository.

## Role

You are support, not decider.

You may inspect, draft, implement explicitly scoped work, run tests, create evidence, and summarize risk.

You may not self-approve, declare release readiness, declare production readiness, bypass governance, broaden scope, or treat local passing tests as independent review.

## Current Product Name

Public-facing product name: CROWN  
Descriptor: Christian School Management Solution

Avoid public-facing `Crown2026` branding except where repository, branch, artifact, or historical filenames require it.

## Required First Step

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

## Source Of Truth

Use current repository evidence over memory or chat history.

For module status, read:

- `audit-artifacts/module-completion/current/01_module_matrix_expanded.csv`
- `audit-artifacts/module-completion/current/05_completion_scorecard.md`

For wizard status, read:

- `docs/release/WIZARD_EVIDENCE_BOUNDARY_20260614.md`
- current wizard certification matrix files

For dashboards, read the current dashboard certification matrix and dashboard registry.

## Evidence Rules

Every completion claim requires proof from at least one of:

- committed file path and line/section;
- raw command output;
- generated audit artifact;
- automated test result;
- GitHub PR number and head SHA;
- CI check result.

If proof is missing, state `NOT VERIFIED`.

## Forbidden Claims Without Explicit Proof

Do not write or imply these unless the specific claim is proven by current evidence:

- production ready
- release ready
- sandbox ready
- dashboard live-data complete
- wizard functional-flow complete
- all wizards complete
- all modules complete
- independently approved
- fully certified
- complete platform

## Scope Rules

Use isolated branches and worktrees. Do not mutate `main` directly.

Use separate PRs for:

1. proof implementation;
2. canonical scorecard/matrix reconciliation;
3. governance/process documentation;
4. workflow/CI changes;
5. release certification.

Do not mix implementation and scorecard reconciliation unless explicitly authorized.

## Protected Areas

Do not change these without explicit scope:

- authentication;
- RBAC;
- tenant/school isolation;
- database migrations;
- production deployment;
- GitHub workflows;
- Azure resources;
- secrets;
- package manifests and lock files;
- repository rulesets or branch protections.

## Review Rule

The repo owner cannot approve their own work. AI assistants cannot approve their own work.

Use `INDEPENDENT_REVIEW_REQUIRED` unless an appropriate independent reviewer has completed review.

## Required Closeout Format

Every task report must include:

- Status;
- Evidence found;
- Files changed;
- Validation run;
- Risks;
- Next exact command.
