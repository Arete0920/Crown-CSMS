# Crown2026 Documentation

This directory contains the canonical documentation for Crown2026.

The purpose of this documentation set is to keep architecture, operations, security, evidence, and investor-facing material organized outside the repository root.

## Documentation principles

Documentation in this repository should be:

- canonical
- scoped
- current
- easy to navigate
- aligned to the live codebase and live workflows
- free of one-off root clutter

Do not place ad hoc reports, proof dumps, working notes, or temporary summaries in the repository root when they belong in a documentation subtree.

## Directory map

### `architecture/`

System design, application boundaries, subsystem relationships, data flow, tenancy model, and interface-level design notes.

Use this section for:

- platform structure
- backend and frontend boundaries
- module maps
- contracts and integration notes
- deployment topology summaries
- architecture decision records, if adopted

### `operations/`

Canonical gateway for runbooks, deployment procedures, environment notes, release handling, incident handling, recovery procedures, and operator guidance.

Start with `operations/README.md`. New operational documentation belongs in this directory.

Use this section for:

- deployment runbooks
- rollback procedures
- health-check procedures
- CI and CD operational notes
- rotation and maintenance procedures
- environment readiness guidance

### `ops/`

Legacy supporting operational material pending file-by-file inventory and reconciliation. Do not add new documents here. Material in this directory does not override `operations/README.md` or the Canonical Document Index.

### `security/`

Security posture, disclosure handling, scanning expectations, secret hygiene, dependency and supply-chain controls, and hardening notes.

Use this section for:

- security standards
- hardening decisions
- secret handling guidance
- review and enforcement notes
- control summaries

### `evidence/`

Proof-oriented documents that support release readiness, auditability, validation, and operational trust.

Use this section for:

- release evidence packets
- validation summaries
- proof references
- audit support material
- deterministic build or deploy evidence

### `investor/`

Condensed business-facing and diligence-facing documentation for controlled review.

Use this section for:

- platform overview
- product scope
- execution highlights
- governance summary
- operating discipline
- current hardening priorities

### `archive/`

Material preserved for historical reference but no longer treated as canonical.

Do not rely on archived material without checking whether a newer canonical document supersedes it.

## Recommended reading order

For a new technical reviewer:

1. `../README.md`
2. `architecture/README.md`
3. `operations/README.md`
4. `security/README.md`
5. `evidence/README.md`

For an investor, diligence reviewer, or executive stakeholder:

1. `investor/README.md`
2. `evidence/README.md`
3. `security/README.md`

## Contribution rules for documentation

When updating documentation:

- prefer updating an existing canonical document over creating a new near-duplicate
- keep file names clear and durable
- avoid redundant summaries when a source-of-truth document already exists
- move stale or superseded material into `archive/`
- keep the repository root minimal
- place new operational documentation under `operations/`, not `ops/`

## Naming guidance

Preferred examples:

- `architecture/platform-overview.md`
- `operations/deployment-runbook.md`
- `security/secret-handling.md`
- `evidence/release-v0.4.0-rc1.md`
- `investor/platform-overview.md`

Avoid vague names such as:

- `notes.md`
- `misc.md`
- `summary-final.md`
- `new-readme.md`
- `checklist2.md`

## Sensitive material

Do not place live secrets, tokens, credentials, private customer data, or unredacted operational material in this directory.

Security-sensitive findings should follow the private handling process documented in `../SECURITY.md`.

## Status

This documentation set is intended to become the canonical home for materials that were previously scattered across the repository root.

Where duplicates exist, the newest clearly designated canonical document should control.