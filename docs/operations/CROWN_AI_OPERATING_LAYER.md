# CROWN AI Operating Layer

## Purpose

This document defines the working AI support layer for CROWN so ChatGPT, GitHub connector, VS Code, Copilot, Microsoft/Azure tools, and future agents improve speed without reducing accuracy, hygiene, or governance.

## Operating Model

CROWN uses a three-lane AI model:

1. Strategy and governance lane: ChatGPT Project or CROWN GPT.
2. Repo-truth lane: GitHub connector and PR/check evidence.
3. Execution lane: VS Code and GitHub Copilot in isolated worktrees.

No AI lane is an approval authority.

## Lane Responsibilities

### ChatGPT Project / CROWN GPT

Primary use:
- current-state audit synthesis;
- proof boundary enforcement;
- work-order drafting;
- scorecard interpretation;
- PR risk review;
- next-step sequencing;
- owner-ready instructions.

Required knowledge files:
- current module matrix;
- current completion scorecard;
- wizard evidence boundary;
- dashboard certification matrix;
- CROWN branding and product taxonomy;
- governance and no-self-approval rules;
- recent merged PR summaries.

### GitHub Connector

Primary use:
- inspect live files on `main`;
- verify PR state, head SHA, merge state, changed files, and workflow runs;
- open bounded governance or work-order branches;
- create proof instruction files;
- avoid stale local assumptions.

Required behavior:
- verify before claiming;
- cite file paths, PRs, and SHAs;
- separate merged facts from pending work;
- never assume a local branch reflects remote truth.

### VS Code / GitHub Copilot

Primary use:
- local implementation;
- focused test creation;
- command execution;
- evidence packet generation;
- diff review.

Required behavior:
- use `.github/copilot-instructions.md`;
- use `.github/instructions/crown-proof-work.instructions.md`;
- run from clean worktrees;
- close every task with changed-file list and validation output;
- do not perform broad edits.

### Microsoft 365 / Entra / Azure

Primary use now:
- tenant identity evidence;
- license evidence;
- conditional access and governance evidence;
- app registration inventory if needed.

Not primary use now:
- do not pause CROWN proof closure to build Azure agents.

Possible later use:
- Copilot Studio internal support agent;
- Azure AI Foundry production CROWN assistant;
- Entra-protected enterprise app integration.

## Recommended Tooling Now

Immediate additions:

1. Keep `.github/copilot-instructions.md` current.
2. Keep reusable instructions in `.github/instructions/`.
3. Use work-order files for every proof lane.
4. Use timestamped evidence packets.
5. Use GitHub connector for remote truth before local execution.
6. Use VS Code/Copilot for local edits only inside allowed scope.
7. Use separate proof PR and reconciliation PR when a module status changes.

Do not add Azure agents yet unless the work is specifically to build an embedded CROWN AI feature.

## CROWN GPT Blueprint

Name:
CROWN Proof and Release Support

Purpose:
Support CROWN development, audit, proof closure, and release-readiness governance.

Instructions:
- Use evidence-first reasoning.
- Treat GitHub connector evidence as current repo truth.
- Never claim production readiness without explicit proof.
- Never claim independent approval unless an independent reviewer has approved.
- Never treat route/API contract validation as full wizard functional-flow completion.
- Never treat mapped dashboards as live-data certification.
- Use CROWN public branding, not Crown2026 public branding.
- Prefer direct PowerShell and VS Code commands.
- Keep claims narrow and proof-backed.

Knowledge files to attach:
- `audit-artifacts/module-completion/current/01_module_matrix_expanded.csv`
- `audit-artifacts/module-completion/current/05_completion_scorecard.md`
- `docs/release/WIZARD_EVIDENCE_BOUNDARY_20260614.md`
- current dashboard certification matrix
- CROWN strategy/product taxonomy materials
- governance/no-self-approval instructions

Capabilities:
- file analysis;
- code review support;
- work-order drafting;
- release evidence synthesis;
- no autonomous approval.

## Agent Readiness Decision

Current decision:
Do not build Azure or Copilot Studio agents as the next sprint blocker.

Rationale:
- remaining module proof closure is repo/test/evidence work;
- GitHub connector plus VS Code/Copilot is already the fastest path;
- agent buildout would add platform setup burden before it produces proof closure.

When to revisit:
- after remaining NOT_PROVEN modules are closed;
- after wizard functional-flow certification has a stable harness;
- after dashboard live-data validation has repeatable evidence;
- when CROWN needs an embedded tenant-facing or staff-facing AI assistant.

## Accuracy Rules

Every AI-generated status must distinguish:

- VERIFIED: supported by current file/PR/command evidence;
- NOT VERIFIED: plausible but not proven;
- NOT DONE: proven absent or failing;
- BLOCKED: cannot proceed without a named dependency;
- OUT OF SCOPE: outside the current work order.

## Efficiency Rules

To move quickly without damage:

1. Work one branch per proof target.
2. Use exact expected-file lists.
3. Run focused tests first.
4. Run broader gates only after focused tests pass.
5. Do not open scorecard reconciliation until proof PR is merged.
6. Do not mix documentation-only reconciliation with implementation changes.
7. Do not allow assistants to approve their own work.

## Current Default Next Work Pattern

For a NOT_PROVEN module:

1. GitHub connector verifies current matrix blocker.
2. Connector opens a work-order branch and file.
3. VS Code creates a clean local worktree.
4. VS Code runs inventory script and baseline checks.
5. Copilot adds minimal proof tests and supporting code.
6. Tests pass locally.
7. PR opens with bounded proof claim.
8. Checks pass.
9. Head-locked merge occurs.
10. Separate canonical reconciliation PR updates matrix/scorecard.

## Non-Negotiables

- No guessing.
- No broad rewrites.
- No hidden background work.
- No self-approval.
- No production/release claim without proof.
- No dashboard live-data claim from route mapping alone.
- No wizard completion claim from route/API contract alone.
