# CROWN Documentation

This directory contains CROWN architecture, engineering, operations, security, evidence, and controlled diligence material.

## Documentation principles

Documentation in this repository should be:

- canonical or clearly classified;
- scoped and current;
- easy to navigate;
- aligned to the live codebase and workflows;
- free of temporary root clutter;
- explicit about evidence boundaries and unresolved risk.

Do not place ad hoc reports, proof dumps, copied conversations, working notes, or temporary summaries in the repository root when they belong in a documentation or evidence subtree.

## Directory map

### `canonical/`

Repository structure, document authority, and current navigation rules.

### `architecture/`

System design, runtime boundaries, data flow, tenancy, domain ownership, interfaces, deployment topology, and architecture decision records.

### `engineering/`

Developer setup, contribution practices, testing, local work controls, and engineering policy.

### `operations/`

Canonical gateway for deployment, rollback, restore, maintenance, incident response, secret rotation, and operator guidance. Start with `operations/README.md`.

### `ops/`

Legacy supporting material pending file-by-file reconciliation. Do not add new material here. It does not override canonical operations documentation.

### `security/`

Security posture, disclosure handling, secret hygiene, dependency and supply-chain controls, hardening decisions, and evidence boundaries.

### `evidence/`

Proof-oriented material supporting validation, auditability, release decisions, and operational trust.

### `investor/`

Controlled technical-diligence material for prospective owners, authorized investors, strategic partners, and executive reviewers. Start with `investor/README.md`.

### `archive/`

Historical or superseded material retained for reference. Archived material is not current authority.

## Recommended reading order

For a technical reviewer or successor:

1. `../README.md`
2. `canonical/REPOSITORY_MANIFEST.md`
3. `canonical/CANONICAL_DOCUMENT_INDEX.md`
4. `engineering/DEV_SETUP.md`
5. `CURRENT_RELEASE_STATUS.md`
6. `operations/README.md`
7. `../SECURITY.md`

For a prospective owner or diligence reviewer:

1. `investor/README.md`
2. `CURRENT_RELEASE_STATUS.md`
3. `canonical/REPOSITORY_MANIFEST.md`
4. `engineering/DEV_SETUP.md`
5. `operations/README.md`
6. `../SECURITY.md`

## Contribution rules

When updating documentation:

- update an existing canonical source instead of creating a near-duplicate;
- use durable file names and explicit status labels;
- move stale or superseded narrative material out of active navigation;
- preserve required history, attribution, licenses, and audit evidence;
- keep product, architecture, implementation, security, testing, approval, and release authority human-owned;
- do not represent generated evidence or a passing subset of checks as universal certification;
- place new operational documentation under `operations/`, not `ops/`.

## Sensitive material

Do not place live secrets, tokens, credentials, private customer data, production database content, private certificates, or unredacted operational material in this directory. Follow `../SECURITY.md` for private vulnerability handling.

## Authority

The Canonical Document Index determines which documents are current authority. When duplicates exist, the latest explicitly designated canonical source controls.
