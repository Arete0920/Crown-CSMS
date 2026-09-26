# CROWN

Christian School Management Solution

## Current posture

CROWN is maintained under controlled software-engineering and release-management practices. The exact current release posture is governed by [docs/CURRENT_RELEASE_STATUS.md](docs/CURRENT_RELEASE_STATUS.md) and the exact repository head being evaluated.

- Product and repository engineering baseline: established
- Security and dependency controls: enforced through CI and review gates
- Current release identity: exact Git/GitHub source at the decision point
- Production deployment/runtime identity: environment-specific and separately verified
- Payment processing: disabled until provider selection, contracting, implementation, and provider-specific certification are complete

## Start here

1. [Investor Technical Review Guide](docs/INVESTOR_TECHNICAL_REVIEW_GUIDE.md)
2. [Current Release Status](docs/CURRENT_RELEASE_STATUS.md)
3. [Canonical Document Index](docs/canonical/CANONICAL_DOCUMENT_INDEX.md)
4. [Diligence and Evidence Index](docs/canonical/DILIGENCE_EVIDENCE_INDEX.md)
5. [Architecture Map](docs/architecture/ARCHITECTURE_MAP.md)
6. [Developer Setup](docs/engineering/DEV_SETUP.md)
7. [Engineering Accountability Policy](docs/engineering/ENGINEERING_ACCOUNTABILITY_POLICY.md)
8. [Code Quality Standard](docs/engineering/CODE_QUALITY_AND_PROVENANCE_STANDARD.md)
9. [Operations](docs/operations/README.md)
10. [Owner Handoff](docs/ownership/OWNER_HANDOFF.md)
11. [Known Limitations](docs/KNOWN_LIMITATIONS.md)
12. [Security Policy](SECURITY.md)

## Authority and claim boundary

Current claims must be supported by current repository evidence, exact-head CI results, retained artifacts, and environment-specific runtime evidence where applicable. Historical commits, tags, workflow runs, pull requests, issues, and predecessor documents remain provenance rather than current operating authority.

## Repository standards

Use one pull request per coherent, independently reversible outcome. Record the exact base and head, scope, validation, limitations, decision owner, and rollback action. Review changed lines against current repository truth and trace failures to their source before changing code or documentation.

Automated tests, static analysis, security scans, dependency audits, and other CI checks are engineering evidence. Human owners remain responsible for architectural decisions, business rules, acceptance decisions, and release authority.

Never commit secrets, production data, private certificates, confidential communications, payment credentials, copied conversations, or generated proof dumps. Sandbox data must be synthetic and clearly labeled.

## Ownership and contribution records

CROWN was created and directed by TC Megahan. Contributor and collaborator attribution must follow durable repository evidence and the current contribution ledger; general early involvement must not be converted into unsupported claims about specific work.

Detailed engineering-accountability and attribution records are governed by the [Engineering Accountability Policy](docs/engineering/ENGINEERING_ACCOUNTABILITY_POLICY.md) and the [Contribution Evidence Ledger](docs/engineering/CONTRIBUTION_EVIDENCE_LEDGER.md).
