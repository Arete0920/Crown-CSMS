# CROWN Known Limitations and Release Disposition

**Status:** Canonical limitations register  
**Last reconciled:** 2026-08-07  
**Certified release:** `17573fb649f74a3ba0f1b3fbc9e004108b3cf228`  
**Immutable tag:** `prod-deploy-20260804-17573fb`  
**Controlling authority:** GitHub issue #1619

## Current disposition

- Bounded repository and production certification: **PASS / COMPLETE**
- Supported-role RBAC and tenant certification: **PASS / COMPLETE**
- Founder/Product Owner authorization: **RECORDED / ACCEPTED**
- Payment processing: **DISABLED / FAIL CLOSED / NEW-OWNER ACTION**
- Buyer diligence package: **READY**
- Actual buyer turnover: **PENDING IDENTIFIED BUYER AND PARTY ACCEPTANCE**

## Certified-scope limitations

- Certification is bounded to the exact SHA, tag, deployment, routes, roles, and evidence recorded in #1619.
- Parent, student, board, and auditor dashboards are not claimed as certified active personas.
- Post-release commits do not silently replace the certified deployment.
- Repository source presence does not establish completion of every dashboard, module, wizard, integration, or optional capability.
- External payment processing is not selected, contracted, enabled, or certified.

## Disclosed residual operational maturity

The following remain visible but were accepted as non-blocking for the bounded release:

- full rollback and isolated operational-backup restore with measured RTO/RPO;
- exhaustive credential rotation, revocation, failed-rotation recovery, and break-glass;
- expanded alert escalation and incident tabletop;
- exhaustive vendor, DPA, region, subprocessor, jurisdiction, and contractual reconciliation;
- synthetic correction, export, deletion, legal-hold, and restored-backup lifecycle exercises;
- historical Git rewrite of the retired key;
- payment-provider integration and activation;
- buyer-controlled account creation, transfer, and seller-access removal.

A buyer, insurer, auditor, counsel, contract, or future owner may make any of these a transaction or operating condition.

## Privacy and legal boundary

CROWN is not represented as FERPA certified, COPPA certified, universally compliant, regulator approved, or suitable for every customer or jurisdiction. Contracts, notices, subprocessors, retention and deletion practices, operating facts, and intended markets require qualified review.

## Handoff boundary

Repository readiness for diligence is not completed buyer turnover. External services, billing, domains, certificates, cloud resources, credentials, contracts, licenses, intellectual property, support responsibilities, and operating authority transfer separately under `docs/ownership/OWNER_HANDOFF.md`.

## Historical-material rule

Older NO-GO records, candidate SHAs, lane plans, release boards, and completion claims are historical unless explicitly retained as current authority. They must not override #1619, the immutable tag, `docs/CURRENT_RELEASE_STATUS.md`, or current exact-identity evidence.
