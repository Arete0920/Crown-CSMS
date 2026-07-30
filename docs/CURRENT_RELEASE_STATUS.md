# CROWN Current Release Status

**Date:** 2026-07-30  
**Repository:** `tcmegahan/Crown2026`  
**Current observed main SHA:** `85072d077476bc40cd52ac1cebe6c53faffa580d`  
**Last functional containment SHA:** `73739d958dd13a5f240782950a6ae19142396d2b`

## Canonical decision

CROWN remains under an **owner-directed repository freeze with bounded remediation permitted**.

- Production: **NOT APPROVED / NO-GO / HOLD**
- Buyer operational turnover: **NOT APPROVED**
- External payment processing: **DEFERRED, DISABLED, AND REQUIRED TO FAIL CLOSED**
- Controlled diligence and explicitly authorized demonstrations: permitted only with accurate disclosures

The eight-lane production-readiness and buyer-handoff program is open under issue #1619. Reopening the program does not establish PASS, completion, certification, production readiness, or buyer readiness.

## Current program posture

The following evidence programs remain incomplete:

1. authenticated deployed-runtime and complete production-surface certification;
2. role, RBAC, tenant-isolation, canonical-identity, and audit certification;
3. application rollback and isolated database restore drills with measured RTO/RPO;
4. operational secret retrieval, rotation, failed-rotation recovery, revocation, and break-glass exercises;
5. student-data privacy, contractual, jurisdiction-specific, incident-response, and qualified legal readiness;
6. deterministic same-SHA CI, deployment, infrastructure, observability, and monitoring proof;
7. final release documentation, evidence index, and buyer-handoff reconciliation;
8. final Founder/Product Owner production authorization.

No issue state, pull request, automated workflow result, documentation update, or repository-only check may be interpreted as satisfying these requirements without the lane's complete linked evidence.

## Current repository identity and evidence boundary

Current observed `main` at this update:

`85072d077476bc40cd52ac1cebe6c53faffa580d`

This SHA includes bounded repository cleanup, CI-authority repairs, compliance evidence work, and a Lane 2 authorization-test repair. It is not an approved production release candidate and has not been certified across deployment, runtime, recovery, secrets operations, privacy/legal readiness, or final authorization.

The last functional containment commit remains:

`73739d958dd13a5f240782950a6ae19142396d2b`

## Security containment boundary

The historical Ed25519 private-key path remains a material unresolved history boundary:

`solomon_governance_c1/governance/c1/runtime/audit_pack/20260515T185051Z/crypto_attestation/ed25519_private_key_DO_NOT_SHARE.pem`

The following must not be claimed as complete without separate evidence:

- exposed-key retirement or revocation;
- replacement-key registration;
- protected-ref history rewrite;
- removal from all retained branches, tags, forks, mirrors, caches, artifacts, releases, or bundles;
- creation and verification of a clean distributable diligence bundle.

Pre-remediation evidence must remain restricted and must not be represented as a clean distribution artifact.

## Scope and exclusions

### Payment processing

No payment processor is approved for production operation. Card, ACH, autopay, processor webhook, refund, and external payment-confirmation paths must remain disabled unless a future owner-authorized program implements and certifies them.

Provider-neutral accounting, billing, ledger, invoice, balance, payment-record, and payment-plan source material may be retained for diligence. Its presence does not establish production fitness.

### Buyer and successor handoff

No buyer, successor, or new owner has been approved. Repository preservation and diligence preparation do not constitute operational transfer, acceptance, or readiness.

### Compliance claims

CROWN may be described only as designed to support schools in meeting applicable student-data privacy and security obligations. It must not be described as FERPA certified, COPPA certified, universally compliant, regulator approved, or compliance guaranteed.

## Repository operation during freeze

Permitted changes are limited to:

- security containment and factual correction;
- removal or disabling of stale automation;
- cleanup of obsolete, duplicate, generated, or misleading material;
- preservation work that does not imply release approval;
- owner-authorized diligence preparation;
- bounded remediation explicitly tied to the open eight-lane program.

A production restart requires:

1. explicit Founder/Product Owner authorization;
2. a newly selected immutable release candidate;
3. fresh same-SHA repository, deployment, runtime, operational, privacy/legal, and recovery evidence;
4. a new explicit GO/NO-GO decision.

## Current final status

**REPOSITORY STATE: FROZEN WITH BOUNDED REMEDIATION**  
**PRODUCTION DECISION: NOT APPROVED / NO-GO / HOLD**  
**BUYER TURNOVER: NOT APPROVED**  
**PAYMENT PROCESSING: DISABLED / FAIL CLOSED**  
**HISTORY REMEDIATION: NOT VERIFIED COMPLETE**
