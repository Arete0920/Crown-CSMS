# CROWN

Christian School Management Solution

## Current posture

**CROWN is production-ready from a product and repository-engineering standpoint.** The current Crown-CSMS `main` containing the formal certification record is the production-ready source baseline.

- Production-ready engineering certification: **PASS**
- Product/repository readiness: **PASS**
- Current repository and release identity: governed by [`docs/CURRENT_RELEASE_STATUS.md`](docs/CURRENT_RELEASE_STATUS.md) and exact current `main`
- Certification record: [`docs/release/CROWN_PRODUCTION_READY_ENGINEERING_CERTIFICATION_20260818.md`](docs/release/CROWN_PRODUCTION_READY_ENGINEERING_CERTIFICATION_20260818.md)
- Successor migration and engineering gap-closure program: **COMPLETED / HISTORICAL PROGRAM RECORD**
- Successor production deployment/runtime identity: **TRANSACTION-TIME / NOT YET ASSERTED**
- Operational rollback and restore mechanics: **RUNNABLE / ENGINEERING-READY; SELECTED-ENVIRONMENT EXECUTION IS TRANSACTION-TIME**
- Buyer operational turnover: **POST-CONTRACT / PENDING AUTHORIZED PARTY ACCEPTANCE**
- Payment processing: **DISABLED / FAIL CLOSED / NOT AUTHORIZED FOR ACTIVATION**

Production-ready engineering certification is not a claim that a successor-controlled production environment is already deployed or accepted. Deployment, runtime identity, production monitoring, credential transfer, operational recovery exercises, payment-provider activation, and final successor acceptance remain separate authorized execution activities.

## Start here

1. [Current Release Status](docs/CURRENT_RELEASE_STATUS.md)
2. [Production-Ready Engineering Certification](docs/release/CROWN_PRODUCTION_READY_ENGINEERING_CERTIFICATION_20260818.md)
3. [Canonical Document Index](docs/canonical/CANONICAL_DOCUMENT_INDEX.md)
4. [Diligence and Evidence Index](docs/canonical/DILIGENCE_EVIDENCE_INDEX.md)
5. [Architecture Map](docs/architecture/ARCHITECTURE_MAP.md)
6. [Developer Setup](docs/engineering/DEV_SETUP.md)
7. [Operations](docs/operations/README.md)
8. [Owner Handoff](docs/ownership/OWNER_HANDOFF.md)
9. [Known Limitations](docs/KNOWN_LIMITATIONS.md)
10. [Security Policy](SECURITY.md)

## Authority and claim boundary

Current claims must be supported by Crown-CSMS exact-identity evidence and current canonical records. Historical commits, tags, workflow runs, pull requests, issues, and predecessor documents remain provenance, not current operating authority.

Automated assistance and automated review are technical evidence, not independent human review, approval, certification, acceptance, or release authority. Where the project uses its approved solo-developer governance workaround, that workaround must be identified accurately rather than represented as independent review.

## Repository standards

Use one pull request per coherent, independently reversible outcome. Record the exact base and head, scope, validation, limitations, decision owner, and rollback action. Review every changed line against current repository truth and trace any failure from the exact failing line through the affected source before changing code or documentation.

Never commit secrets, production data, private certificates, confidential communications, payment credentials, copied conversations, or generated proof dumps. Sandbox data must be synthetic and clearly labeled.

## Ownership and contribution records

CROWN was created and directed by TC Megahan. Contributor and collaborator attribution must follow durable repository evidence and the current contribution ledger; general early involvement must not be converted into unsupported claims about specific work.

Detailed attribution and development-process records are governed by the [Human Accountability and Development Assistance Policy](docs/engineering/HUMAN_ACCOUNTABILITY_AND_DEVELOPMENT_ASSISTANCE_POLICY.md) and the [Contribution Evidence Ledger](docs/engineering/CONTRIBUTION_EVIDENCE_LEDGER.md).
