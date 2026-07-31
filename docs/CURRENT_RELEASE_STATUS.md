# CROWN Current Release Status

**Date:** 2026-07-31  
**Repository:** `tcmegahan/Crown2026`  
**Last observed main before this documentation change:** `d725386a6cfbb48f9967e65e15cd92db27cdfde2`  
**Status basis:** live repository state and controlling issue `#1619`

## Canonical decision

CROWN remains under **bounded remediation before selection of a future immutable release candidate**.

- Production: **NOT APPROVED / NO-GO / HOLD**
- Buyer operational turnover: **NOT APPROVED**
- External payment processing: **DEFERRED, DISABLED, AND REQUIRED TO FAIL CLOSED**
- Controlled diligence and explicitly authorized demonstrations: permitted only with accurate disclosures

GitHub issue `#1619` and its eight lane issues are the sole controlling production-readiness and buyer-handoff framework. Repository checks, issue closure, pull-request completion, documentation updates, or partial evidence do not establish production or buyer readiness.

## Current program posture

The following evidence programs remain incomplete:

1. authenticated deployed-runtime and complete production-surface certification;
2. role, RBAC, tenant-isolation, canonical-identity, and audit certification;
3. application rollback and isolated database restore drills with measured RTO/RPO;
4. operational secret retrieval, rotation, failed-rotation recovery, revocation, and break-glass exercises;
5. student-data privacy, contractual, jurisdiction-specific, incident-response, and qualified legal readiness;
6. deterministic same-SHA CI, deployment, infrastructure, observability, and monitoring proof;
7. final release documentation, evidence index, runbook, and buyer-handoff reconciliation;
8. final Founder/Product Owner production authorization.

## Repository identity and evidence boundary

The last observed `main` before this documentation change was:

`d725386a6cfbb48f9967e65e15cd92db27cdfde2`

That SHA includes the merged provider-neutral payment containment work from PR `#1796` and the tests-only tenant-safe export coverage tranche from PR `#1799`. It is not an approved production release candidate and has not been certified across deployment, runtime, recovery, secrets operations, privacy/legal readiness, or final authorization. Its authoritative exact coverage percentage remains subject to a dedicated coverage run against that unchanged SHA.

Merging this or any later change necessarily creates a different `main` identity. Therefore, the live current `main` SHA must always be resolved directly from the repository and may not be inferred from this document. No documentation or source change may be represented as covered by evidence collected for `d725386a6cfbb48f9967e65e15cd92db27cdfde2` without fresh exact-SHA verification.

## Security containment boundary

The historical Ed25519 private-key path remains a material unresolved history boundary:

`solomon_governance_c1/governance/c1/runtime/audit_pack/20260515T185051Z/crypto_attestation/ed25519_private_key_DO_NOT_SHARE.pem`

The following must not be claimed complete without separate evidence:

- exposed-key retirement or revocation;
- replacement-key registration;
- protected-ref history rewrite;
- removal from all retained branches, tags, forks, mirrors, caches, artifacts, releases, or bundles;
- creation and verification of a clean distributable diligence bundle.

Pre-remediation evidence must remain restricted and must not be represented as a clean distribution artifact.

## Payment-processing boundary

No payment processor is approved for production operation. Card, ACH, autopay, processor webhook, refund, settlement, dispute, and external payment-confirmation paths must remain disabled unless a future owner-authorized program implements and certifies them.

Provider-neutral accounting, billing, ledger, invoice, balance, payment-record, and payment-plan source material may be retained for diligence. Its presence does not establish production fitness.

## Buyer and successor handoff

No buyer, successor, or new owner has been approved for operational turnover. Repository preservation and diligence preparation do not constitute operational transfer, acceptance, or readiness.

## Compliance claim boundary

CROWN may be described only as designed to support schools in meeting applicable student-data privacy and security obligations. It must not be described as FERPA certified, COPPA certified, universally compliant, regulator approved, or compliance guaranteed.

## Repository operation during bounded remediation

Permitted changes are limited to:

- security containment and factual correction;
- removal or disabling of stale automation;
- cleanup of obsolete, duplicate, generated, or misleading material;
- preservation work that does not imply release approval;
- owner-authorized diligence preparation;
- bounded remediation explicitly tied to the open eight-lane program.

A production restart requires:

1. completion of all authorized repository-changing work;
2. explicit re-establishment of repository freeze;
3. selection of one immutable release candidate;
4. fresh same-SHA repository, deployment, runtime, operational, privacy/legal, and recovery evidence;
5. explicit Founder/Product Owner authorization and a new GO/NO-GO decision.

## Current final status

**REPOSITORY STATE: BOUNDED REMEDIATION; NO IMMUTABLE RC SELECTED**  
**PRODUCTION DECISION: NOT APPROVED / NO-GO / HOLD**  
**BUYER TURNOVER: NOT APPROVED**  
**PAYMENT PROCESSING: DISABLED / FAIL CLOSED**  
**HISTORY REMEDIATION: NOT VERIFIED COMPLETE**
