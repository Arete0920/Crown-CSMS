# CROWN Diligence and Evidence Index

**Status:** Canonical diligence navigation authority  
**Owner:** Founder/Product Owner  
**Effective date:** 2026-07-29  
**Repository basis:** `tcmegahan/Crown2026`  
**Observed source identity at creation:** `591975fe67eae4564e60e3c00229c1928d5b8d49`

## Purpose

This index is the single repository navigation point for technical diligence, ownership-transfer preparation, release posture, architecture, security, operations, recovery, compliance boundaries, and known limitations.

It does not certify production readiness, buyer readiness, legal compliance, security certification, recovery capability, or payment-processor readiness. Evidence must apply to one identified immutable source SHA and, where applicable, the same deployed runtime identity.

## Current controlling posture

The controlling release and freeze authority is:

- `docs/CURRENT_RELEASE_STATUS.md`

Current repository posture:

- repository state: frozen;
- production: not approved / no-go / hold;
- buyer operational turnover: not approved;
- external payment processing: deferred, disabled, and required to fail closed;
- protected-history remediation: not verified complete.

No historical issue closure, pull request, workflow result, dated release record, generated report, or source-file existence overrides the current release authority.

## Canonical navigation

| Area | Canonical source | What it establishes |
|---|---|---|
| Repository orientation | `README.md` | Entry point, scope, and repository posture |
| Repository structure | `docs/canonical/REPOSITORY_MANIFEST.md` | Active source and documentation boundaries |
| Documentation authority | `docs/canonical/CANONICAL_DOCUMENT_INDEX.md` | Which documents are authoritative |
| Documentation gateway | `docs/README.md` | Current documentation organization and reading order |
| Architecture gateway | `docs/architecture/README.md` | Architecture entry point |
| Architecture map | `docs/architecture/ARCHITECTURE_MAP.md` | Current system boundaries and component relationships |
| Architecture decisions | `docs/architecture/DECISION_INDEX.md` | Accepted, superseded, and pending architecture decisions |
| Implementation overview | `docs/architecture/SYSTEM_OVERVIEW.md` | Source-grounded implementation summary |
| Developer setup | `docs/engineering/DEV_SETUP.md` | Reproducible development setup expectations |
| Operations gateway | `docs/operations/README.md` | Deployment, maintenance, rollback, restore, incidents, and operational controls |
| Security reporting | `SECURITY.md` | Vulnerability reporting and sensitive-information handling |
| Ownership transfer | `docs/ownership/OWNER_HANDOFF.md` | Repository and external-service transfer requirements |
| Development provenance | `docs/provenance/CROWN_DEVELOPMENT_PROVENANCE.md` | Controlled lineage and contributor attribution |
| Current release posture | `docs/CURRENT_RELEASE_STATUS.md` | Canonical no-go, freeze, payment, and history-remediation authority |
| Known limitations | `docs/KNOWN_LIMITATIONS.md` | Current limitations and unverified boundaries |

## Eight-lane evidence status

The controlling program is GitHub issue `#1619`. The lane issues remain evidence requirements and are not satisfied by documentation alone.

| Lane | Issue | Repository documentation state | Evidence status |
|---|---:|---|---|
| Runtime and complete surface certification | `#1620` | Surface ledgers and verification tooling exist | **UNPROVEN** — deployed authenticated persona and complete-surface certification not established on one current SHA |
| Identity, RBAC, tenant isolation, and audit | `#1626` | Architecture and source controls exist | **UNPROVEN** — complete cross-role, cross-tenant, object-level, escalation-denial, and audit certification not established |
| Rollback, restore, resilience, RTO/RPO | `#1627` | Operational guidance exists | **UNPROVEN** — application rollback and isolated database restore drills with measured RTO/RPO not completed |
| Secrets and privileged access | `#1628` | Secret-scanning and redacted adjudication records exist | **UNPROVEN** — protected-history rewrite, key retirement, rotation, revocation, failed-rotation recovery, and break-glass exercises not verified complete |
| Privacy, records, contracts, and legal readiness | `#1629` | Security and product controls exist | **UNPROVEN** — complete data map, retention/deletion, incident, contract, and qualified legal reconciliation not completed |
| CI/CD, infrastructure, observability, exact-SHA deployment | `#1630` | CI and deployment definitions exist | **UNPROVEN** — terminal same-SHA CI, deployed identity, monitoring, and infrastructure evidence are not complete for a current immutable release candidate |
| Documentation, diligence, and owner handoff | `#1631` | Canonical documentation and this index exist | **DOCUMENTATION RECONCILED; EXTERNAL EVIDENCE DEPENDENCIES REMAIN** |
| Final production and buyer authorization | `#1632` | Decision criteria are documented | **NOT AUTHORIZED** — prerequisite lanes have not passed on one immutable release identity |

## Security and history-remediation boundary

The historical Ed25519 private-key path identified by the current release authority remains a material unresolved history boundary. The following may not be represented as complete without separate verified evidence:

- exposed-key retirement or revocation;
- replacement-key registration;
- protected-ref history rewrite;
- removal from retained branches, tags, forks, mirrors, caches, artifacts, releases, and bundles;
- verification of a clean distributable diligence bundle.

Pre-remediation material must remain restricted and must not be presented as a clean buyer or successor distribution.

## Payment-processing boundary

No payment processor is approved for production. Card, ACH, autopay, processor-webhook, refund, settlement, dispute, and external payment-confirmation paths must remain disabled unless a future owner-authorized program implements and certifies them.

Provider-neutral billing, accounting, ledger, invoice, balance, payment-record, and payment-plan source material may be reviewed for diligence. Source presence does not establish operational or processor readiness.

## Privacy and compliance claim boundary

Repository materials may describe CROWN as designed to support schools in meeting applicable privacy and security obligations. They may not claim:

- FERPA certification;
- COPPA certification;
- universal legal compliance;
- regulator approval;
- guaranteed customer suitability;
- completed jurisdiction-specific legal review.

Those conclusions require current product behavior, operating procedures, contracts, data practices, deployment facts, and qualified legal review.

## Buyer and successor review sequence

A diligence reviewer or authorized successor should proceed in this order:

1. Read `docs/CURRENT_RELEASE_STATUS.md`.
2. Read `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`.
3. Read this index.
4. Review `README.md` and `docs/canonical/REPOSITORY_MANIFEST.md`.
5. Review architecture through `docs/architecture/README.md`.
6. Review setup and reproducibility through `docs/engineering/DEV_SETUP.md`.
7. Review operational controls through `docs/operations/README.md`.
8. Review security handling through `SECURITY.md`.
9. Review ownership-transfer requirements through `docs/ownership/OWNER_HANDOFF.md`.
10. Review open issues `#1619` and `#1620` through `#1632` for live evidence status.
11. Independently verify exact-SHA CI, deployment, runtime, recovery, secret, privacy/legal, and authorization evidence before relying on any readiness claim.

## Historical and non-authoritative material

The repository retains dated release, review, planning, certification, and proof-related files for history or source context. Unless listed in `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`, those files are not current authority and must not override:

- `docs/CURRENT_RELEASE_STATUS.md`;
- `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`;
- accepted decisions listed in `docs/architecture/DECISION_INDEX.md`;
- the live state and evidence in controlling GitHub issues.

Historical documents should be treated as provenance only. Unsupported `SHIP`, `RELEASE_READY`, `100% complete`, certification, compliance, recovery, production, or buyer-readiness language is not current authority.

## Lane 7 completion boundary

This index completes the repository-navigation portion of Lane 7 by providing one canonical, navigable diligence map and explicit claim boundaries.

Lane 7 must not be represented as full buyer-handoff completion until repository documentation is reconciled with current runtime, deployment, recovery, secret, privacy/legal, external-service ownership, and successor-identity evidence. Those dependencies require evidence outside documentation and, in several cases, outside the GitHub connector.
