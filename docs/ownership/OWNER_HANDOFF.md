# CROWN Owner Handoff

**Status:** Canonical transfer guide  
**Last reconciled:** 2026-08-07  
**Certified release:** `17573fb649f74a3ba0f1b3fbc9e004108b3cf228`  
**Immutable tag:** `prod-deploy-20260804-17573fb`  
**Controlling authority:** GitHub issue #1619

## Current operating posture

CROWN completed bounded repository and production certification for the exact release identity above. The repository and product are ready for buyer diligence and transaction-specific transfer.

Actual buyer turnover remains pending an identified buyer, buyer acceptance, successor account creation, approved access transfer, credential rotation, and seller-access removal. External payment processing remains disabled, fails closed, and is deferred to the new owner.

This guide does not expand the certified scope, certify unsupported personas, activate payments, provide legal certification, or claim that buyer-specific transfer actions have occurred.

## Repository start path

1. `README.md`
2. `docs/CURRENT_RELEASE_STATUS.md`
3. GitHub issue #1619
4. `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`
5. `docs/canonical/DILIGENCE_EVIDENCE_INDEX.md`
6. `docs/canonical/REPOSITORY_MANIFEST.md`
7. `docs/architecture/ARCHITECTURE_MAP.md`
8. `docs/engineering/DEV_SETUP.md`
9. `docs/operations/README.md`
10. `SECURITY.md`

## What transfers with the repository

- application source, migrations, tests, and dependency locks;
- CI, deployment, architecture, engineering, security, and operations material;
- canonical diligence navigation and release authority;
- repository history, issues, pull requests, tags, and release lineage.

## External ownership transferred separately

The authorized transaction must inventory and transfer GitHub administration, Azure resources and billing, domains and DNS, certificates, email and Microsoft 365, Entra registrations, monitoring, backups, incident contacts, integration accounts, contracts, licenses, trademarks, and other intellectual-property records. Secret values must never be committed.

## Required transaction controls

1. Identify and authorize the successor.
2. Record buyer acceptance of the certified scope and disclosed residual risks.
3. Add successor-controlled accounts before removing seller access.
4. Transfer external-service ownership and billing.
5. Rotate credentials, keys, certificates, tokens, webhooks, and recovery codes.
6. Update `CODEOWNERS`, repository rules, environment approvers, contacts, and notifications.
7. Verify a clean clone, setup, test, build, and approved deployment path.
8. Verify the exact transferred SHA and deployed identity.
9. Execute any transaction-required rollback, restore, rotation, monitoring, privacy, legal, or insurance work.
10. Record final acceptance and seller-access removal.

## Certified and unresolved boundaries

Seller-complete technical certification is recorded in #1619. The following remain buyer-specific actions or disclosed operational maturity work unless separately executed: measured rollback/restore, exhaustive credential rotation and break-glass, expanded alert and incident exercises, jurisdiction and contract reconciliation, lifecycle data exercises, payment-provider activation, and final access transfer.

Repository transfer alone does not establish legal compliance, payment readiness, customer suitability, or completion of transaction-specific turnover.
