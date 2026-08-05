# CROWN Build and Engineering Rules

**Status:** Active authority map  
**Updated:** 2026-08-05

This file replaces the legacy January 2026 build-rules document, which contained obsolete local paths, stale environment assumptions, outdated branch guidance, deprecated credentials, and tooling-specific collaboration language.

## Current authorities

Use these sources in this order:

1. `AGENTS.md` — repository operating instructions;
2. `docs/engineering/DEV_SETUP.md` — local development and environment setup;
3. `docs/CURRENT_RELEASE_STATUS.md` and GitHub issue `#1619` — release, deployment, payment, and handoff posture;
4. repository workflows and branch rules — required checks and merge controls;
5. module-specific canonical documents — architecture, permissions, tenancy, data ownership, and evidence requirements.

## Non-negotiable engineering rules

- Work on an isolated branch tied to a bounded issue or pull request.
- Record the exact evaluated SHA for every certification or completion claim.
- Do not commit credentials, tokens, private keys, customer data, local databases, generated evidence noise, or editor-specific files.
- Use environment variables or approved secret stores for sensitive configuration.
- Preserve tenant and school isolation in models, services, APIs, background jobs, exports, and direct-object access.
- Require explicit role and action-level authorization for protected operations.
- Add migrations for schema changes and verify forward application on a production-like database.
- Add or update tests for successful behavior, rejected behavior, permissions, tenancy, and regression boundaries.
- Run the required repository checks before merge.
- Do not describe a module, dashboard, workflow, release, or handoff as complete beyond the retained evidence.

## Review and authority boundary

Automated systems may assist with inspection, implementation, testing, analysis, drafting, and evidence organization. They are not human authors, independent reviewers, approvers, acceptance authorities, certification authorities, or release authorities.

A qualified independent reviewer must be a person who did not author the work. Where the approved solo-developer workaround applies, it provides bounded founder verification but does not become independent review or self-approval.

## Change discipline

Before committing:

- inspect `git status` and the complete diff;
- confirm every changed path belongs to the declared scope;
- remove debug output, temporary files, backups, and stale generated artifacts;
- verify tests and checks appropriate to the change;
- update documentation only where the change alters current authority or supported behavior.

This document is an authority pointer and minimum control set. More specific current canonical documents control when they impose stricter requirements.
