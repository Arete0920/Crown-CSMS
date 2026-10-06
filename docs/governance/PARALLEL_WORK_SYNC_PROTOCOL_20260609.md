# CROWN Parallel Work Sync Protocol

Date: 2026-06-09  
Updated: 2026-08-05

## Purpose

Keep repository tools, connectors, local terminals, and worktrees synchronized through durable repository evidence rather than hidden session state.

## Scope

This protocol applies whenever more than one tool, terminal, connector, or worktree is active around CROWN.

Tools do not share private state. Synchronization must happen through retained evidence.

## Required synchronization anchors

Use one or more of these anchors for every active lane:

- pull-request body;
- GitHub issue comment;
- `docs/CURRENT_RELEASE_STATUS.md` for release posture;
- audit packet under the relevant evidence directory;
- product or runtime evidence tied to the evaluated SHA;
- sanitized terminal output from the active workspace.

## Required pre-change packet

Before changing files, record:

1. current branch;
2. current HEAD SHA;
3. worktree status and affected paths;
4. governing issue or pull request;
5. exact task;
6. files expected to change;
7. files explicitly out of scope;
8. validation that will prove the work.

If these items cannot be stated, do not edit.

## Product-lane isolation

A product pull request must contain only files required for its named lane. Do not mix unrelated hygiene cleanup, local backups, stale packets, or unrelated product surfaces into the same change set.

## Human-authority boundary

Development tooling may support inspection, implementation, testing, analysis, drafting, and evidence organization. Tool output does not constitute independent human review, approval, certification, acceptance, or release authority.

Independent review means review by a qualified person who did not author the work. Tool findings are supporting evidence only.

## Required reporting format

Use:

- Status
- Evidence
- Files changed
- Validation
- Risks
- Next controlled action

Do not report completion without evidence tied to the evaluated SHA.
