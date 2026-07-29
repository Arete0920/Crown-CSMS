# CROWN Documentation

This directory contains the current architecture, engineering, operations, security, ownership-transfer, provenance, diligence, and release-authority documentation for CROWN.

## Documentation principles

Documentation must be:

- current or explicitly canonical;
- scoped to architecture, functionality, engineering, security, operation, recovery, diligence, or ownership transfer;
- aligned with the live codebase and active workflows;
- free of generated test output, proof dumps, local workstation captures, commercial strategy, and superseded release narratives;
- explicit about unresolved risk and authority boundaries.

## Directory map

### `canonical/`

Repository structure, document authority, diligence navigation, and documentation rules.

### `architecture/`

System design, runtime boundaries, data flow, tenancy, domain ownership, interfaces, integrations, and deployment topology.

### `engineering/`

Developer setup, contribution practices, testing, and engineering policy.

### `operations/`

Deployment, rollback, restore, maintenance, incident response, secret rotation, and operator guidance. Start with `operations/README.md`.

### `security/`

Security posture, disclosure handling, secret hygiene, dependency controls, and hardening guidance.

### `ownership/`

Repository and external-service transfer requirements. Start with `ownership/OWNER_HANDOFF.md`.

### `provenance/`

Controlled development lineage and attribution records.

## Recommended reading order

1. `../README.md`
2. `canonical/REPOSITORY_MANIFEST.md`
3. `canonical/CANONICAL_DOCUMENT_INDEX.md`
4. `CURRENT_RELEASE_STATUS.md`
5. `canonical/DILIGENCE_EVIDENCE_INDEX.md`
6. `engineering/DEV_SETUP.md`
7. `architecture/`
8. `operations/README.md`
9. `ownership/OWNER_HANDOFF.md`
10. `../SECURITY.md`

## Contribution rules

- Update an existing canonical source instead of creating a near-duplicate.
- Use durable file names and explicit authority labels.
- Do not add dated execution boards, audit reports, generated evidence, copied conversations, marketing plans, or transaction material.
- Keep product, architecture, implementation, security, approval, and release authority human-owned.
- Do not represent source existence or a passing subset of checks as universal certification.
- Place operational documentation under `operations/`, transfer documentation under `ownership/`, and diligence navigation under `canonical/`.

## Sensitive material

Do not commit passwords, API keys, tokens, private customer data, production database content, private certificates, tenant secrets, Microsoft credentials, recovery codes, or unredacted confidential communications. Follow `../SECURITY.md` for private vulnerability handling.

## Authority

`canonical/CANONICAL_DOCUMENT_INDEX.md` determines current documentation authority. `CURRENT_RELEASE_STATUS.md` controls release and freeze posture. `canonical/DILIGENCE_EVIDENCE_INDEX.md` controls diligence navigation and evidence-status claim boundaries.
