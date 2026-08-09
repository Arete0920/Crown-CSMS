# CROWN Repository Work Contract

## Authority

Current GitHub source, canonical documents, exact-head checks, retained artifacts, and deployed-runtime evidence control. Memory, stale status files, missing artifacts, and historical branch names do not.

## Before editing

Record the branch, exact base SHA, one-sentence outcome, allowed files, forbidden files, validation, and rollback.

## Change management

Use one branch and one pull request per coherent, independently reversible outcome. Keep related implementation, tests, documentation, workflow corrections, and review fixes together. A separate PR requires an independent risk or rollback boundary under `docs/governance/CHANGE_MANAGEMENT.md`.

## Evidence

Completion claims require current source, raw command output, retained artifacts, exact-head CI, or deployed-runtime proof. Missing proof is `NOT VERIFIED`. Pending, failed, cancelled, stale, or action-required checks are not PASS.

Do not claim universal completion, production readiness, release readiness, independent approval, or legal compliance beyond the exact current evidence and `docs/CURRENT_RELEASE_STATUS.md`.

## Protected areas

Authentication, RBAC, tenant isolation, migrations, deployment, workflows, cloud resources, secrets, dependencies, rulesets, and branch protection require explicit scope and proportional verification.

## Review

The repository owner cannot independently approve their own work. Automated review is not independent human approval. Use the documented compensating control only where authorized, with exact-head checks, zero unresolved actionable findings, and head-locked merge.
