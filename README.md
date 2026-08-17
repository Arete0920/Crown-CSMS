# CROWN

Christian School Management Solution

## Current posture

Crown-CSMS is the active engineering and owner-turnover repository.

- Current repository identity: the exact commit at GitHub `main`; never substitute a historical PR, migration baseline, or predecessor SHA for current `main`.
- Current release and turnover authority: `docs/CURRENT_RELEASE_STATUS.md` and Crown-CSMS issue #14.
- Production deployment/runtime identity: must be established by exact-source deployment and runtime evidence; repository success alone is not deployment proof.
- Payment processing: **DISABLED / FAIL CLOSED** pending provider selection, contracting, credentials, and separate authorization.

Historical Crown2026 commits, tags, issues, and workflow runs remain provenance and rollback/reference evidence only. They do not control the active Crown-CSMS repository.

## Start here

1. [Current Release Status](docs/CURRENT_RELEASE_STATUS.md)
2. [Canonical Document Index](docs/canonical/CANONICAL_DOCUMENT_INDEX.md)
3. [Diligence and Evidence Index](docs/canonical/DILIGENCE_EVIDENCE_INDEX.md)
4. [Architecture Map](docs/architecture/ARCHITECTURE_MAP.md)
5. [Developer Setup](docs/engineering/DEV_SETUP.md)
6. [Operations](docs/operations/README.md)
7. [Owner Handoff](docs/ownership/OWNER_HANDOFF.md)
8. [Known Limitations](docs/KNOWN_LIMITATIONS.md)
9. [Security Policy](SECURITY.md)

## Exact-identity rule

For handoff, release, audit, or production claims, first resolve the exact GitHub `main` SHA and then verify evidence generated for that same SHA. Any commit invalidates prior head-specific certification. Documentation deliberately does not embed a self-referential “final SHA”; the immutable Git commit being handed off is the source identity.

## Authority and claim boundary

Current claims must be supported by Crown-CSMS exact-identity evidence and current canonical records. Historical commits, tags, workflow runs, pull requests, and issues remain provenance, not current operating authority.

Automated assistance and automated review are technical evidence, not independent human review, approval, certification, acceptance, or release authority. Solo-developer compensating controls are documented and must not be represented as independent review.

## Repository standards

Use one pull request per coherent, independently reversible outcome. Record the exact base and head, scope, validation, limitations, decision owner, and rollback action. Review every changed line against current repository truth and trace any failure from the exact failing line through the affected source before changing code or documentation.

Never commit secrets, production data, private certificates, confidential communications, payment credentials, copied conversations, or generated proof dumps. Sandbox data must be synthetic and clearly labeled.

## Ownership

CROWN was created and directed by TC Megahan, Founder/Product Owner, principal developer, product designer, and architecture and workflow authority. Anthony Rizzo, Ayush Agarwal, and Jed Hansen were founding/early collaborators; specific work is credited only where durable evidence supports it. Johnny Megahan and Evan Lesage are new collaborators and are not assigned historical contributions.

Detailed attribution and development-process records are governed by the [Human Accountability and Development Assistance Policy](docs/engineering/HUMAN_ACCOUNTABILITY_AND_DEVELOPMENT_ASSISTANCE_POLICY.md) and the [Contribution Evidence Ledger](docs/engineering/CONTRIBUTION_EVIDENCE_LEDGER.md).
