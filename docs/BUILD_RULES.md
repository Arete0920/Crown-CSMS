# CROWN Build and Engineering Rules

**Status:** Active authority map  
**Last reconciled:** 2026-08-18

This file is a compact pointer to the current engineering control surface. It replaces predecessor-era build rules that contained obsolete local paths, environment assumptions, credentials, issue authority, and tooling-specific collaboration instructions.

## Current authorities

Use these sources in this order:

1. `AGENTS.md` — repository operating instructions;
2. `docs/canonical/CANONICAL_DOCUMENT_INDEX.md` — current documentation authority;
3. `docs/engineering/DEV_SETUP.md` — local development and environment setup;
4. `docs/CURRENT_RELEASE_STATUS.md` plus exact current Git/GitHub identity — release, deployment-claim, payment, and handoff posture;
5. current repository workflows and live GitHub rules — required checks and merge controls;
6. module-specific canonical documents — architecture, permissions, tenancy, data ownership, and evidence requirements.

Historical predecessor issue numbers, copied SHAs in obsolete documents, and retired repository settings are not current authority.

## Non-negotiable engineering rules

- Work on an isolated branch for a bounded, reviewable change.
- Record the exact evaluated SHA for every certification or completion claim.
- Do not commit credentials, tokens, private keys, customer data, local databases, generated evidence noise, or editor-specific files.
- Use environment variables or approved secret stores for sensitive configuration.
- Preserve tenant and school isolation in models, services, APIs, background jobs, exports, and direct-object access.
- Require explicit role and action-level authorization for protected operations.
- Add migrations for schema changes and verify forward application on the required database class.
- Add or update tests for successful behavior, rejected behavior, permissions, tenancy, and regression boundaries.
- Run the required repository checks for the affected surface before merge.
- Freeze the final candidate head for exact-head certification when release governance requires it.
- Do not describe a module, dashboard, workflow, release, production deployment, or handoff as complete beyond the retained exact evidence.
- Payment processing remains disabled/fail closed unless separately authorized under the current payment governance boundary.

## Review and authority boundary

Automated systems may assist with inspection, implementation, testing, analysis, drafting, and evidence organization. They are not independent human reviewers, approvers, acceptance authorities, legal/compliance authorities, or release authorities.

A qualified independent reviewer is a person who did not author the work and has the required authority. Where an approved compensating-control process applies because an eligible independent reviewer is unavailable, describe that control accurately; it does not become independent review or self-approval.

## Change discipline

Before publishing a candidate:

- inspect the complete diff and changed-path inventory;
- confirm every changed path belongs to the declared scope;
- remove debug output, temporary files, backups, copied proof dumps, and stale generated artifacts;
- verify tests and checks appropriate to the change;
- update documentation only where the change alters current authority, supported behavior, or operator requirements;
- avoid speculative pushes and redundant CI runs, especially when equivalent exact-head evidence already exists.

## Handoff discipline

Repository engineering completion and operational transfer are separate gates. Owner turnover additionally requires the exact selected source/runtime identity, recovery and monitoring evidence or accepted dispositions, successor-controlled accounts and credentials, and authorized acceptance under `docs/ownership/OWNER_HANDOFF.md`.

This document is an authority pointer and minimum control set. More specific current canonical documents control when they impose stricter requirements.
