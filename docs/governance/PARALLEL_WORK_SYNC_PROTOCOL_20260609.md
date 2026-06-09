# CROWN Parallel Work Sync Protocol

Date: 2026-06-09
Purpose: Keep VS Code Copilot, ChatGPT GitHub connector work, and local terminal work synchronized by repository evidence rather than hidden conversation memory.

## Scope

This protocol applies when more than one assistant, tool, terminal, connector, or local worktree is active around CROWN.

The tools do not share private state. Synchronization must happen through durable evidence.

## Required synchronization anchors

Use one or more of these anchors for any active lane:

- PR body;
- GitHub issue comment;
- `docs/CURRENT_RELEASE_STATUS.md` for release posture;
- local audit packet under `audit-artifacts/repo-hygiene/`;
- product/runtime evidence packet under the relevant proof directory;
- pasted terminal output from the active local workspace.

## Required pre-change packet

Before changing files, capture and state:

1. current branch;
2. current HEAD;
3. `git status --porcelain=v1` count and paths;
4. governing issue or PR number;
5. exact task;
6. exact files expected to change;
7. files explicitly out of scope;
8. validation commands that will prove the work.

If those eight items cannot be named, do not edit.

## Hygiene gate

Product work may proceed only when local hygiene is controlled.

Required proof:

- deleted tracked files count is zero unless deletion is explicitly scoped;
- nested repository pending count is zero where nested repositories exist;
- root untracked noise is absent, quarantined outside the product lane, or locally excluded by a reviewed local-only exclude;
- every dirty root entry has an owner decision: KEEP, REVERT, COMMIT-READY, or NEEDS REVIEW;
- NEEDS REVIEW count is zero before commit;
- no audit packet, backup directory, local backup, or hygiene artifact enters a product PR unless explicitly scoped.

## Product lane isolation

A product PR must contain only product files for the named lane.

Examples:

- wizard lane: wizard pages, wizard route tests, wizard API contract tests, wizard docs when explicitly scoped;
- release-certification lane: release-certification scripts and their tests only;
- governance lane: governance docs or authority files only.

Do not mix hygiene cleanup, release evidence, local backups, stale packets, or unrelated dashboards into a wizard PR.

## Release posture rule

Production, sandbox, and full-completion claims require current-head evidence.

Allowed when proof is incomplete:

- NO-GO;
- REVIEW REQUIRED;
- PARTIAL with row-level evidence;
- NOT VERIFIED.

Not allowed without current evidence:

- production ready;
- unrestricted GO;
- all dashboards complete;
- all wizards complete;
- sandbox broadly approved;
- latest head release-certified.

## Wizard done definition

A wizard is not done because a screen exists.

A wizard is PASS only when evidence proves:

1. registry/manifest entry;
2. route/navigation wiring;
3. frontend wizard flow;
4. API/service contract;
5. persistence/model contract where data is saved;
6. role permission enforcement;
7. tenant/school isolation;
8. KPI or operational metric wiring where applicable;
9. seed/demo/sandbox data where applicable;
10. automated tests/proof;
11. documentation/canon entry;
12. audit/event trail where required.

Anything less is REVIEW, FAIL_PARTIAL, or FAIL_MISSING.

## Required reporting format

Use this structure for work reports:

- Status;
- Evidence found;
- Files changed;
- Validation run;
- Risks;
- Next exact command.

Do not report completion without evidence.
