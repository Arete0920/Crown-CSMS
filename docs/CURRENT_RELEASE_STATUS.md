# CROWN Current Release Status

**Date:** 2026-08-04  
**Repository:** `tcmegahan/Crown2026`  
**Certified release source:** `17573fb649f74a3ba0f1b3fbc9e004108b3cf228`  
**Immutable production tag:** `prod-deploy-20260804-17573fb`  
**Production deployment run:** `30944978175`  
**Controlling authority:** GitHub issue `#1619`

## Canonical decision

CROWN has completed repository and production technical certification for the bounded supported release scope identified below.

- Repository release technical gates: **PASS**
- Production deployment and runtime technical gates: **PASS**
- Bounded supported-role, RBAC, and tenant-isolation certification: **PASS**
- Payment processing: **DEFERRED — NEW OWNER; DISABLED; FAIL CLOSED**
- Buyer operational turnover: **NOT YET ACCEPTED — HANDOFF RECONCILIATION AND BUYER ACCEPTANCE PENDING**
- Final production authorization: **PENDING FOUNDER/PRODUCT OWNER DECISION AND ACCEPTANCE OF DISCLOSED RESIDUAL OPERATIONAL RISKS**

This document records the current evidence-backed posture. GitHub issue `#1619` remains the sole controlling production-readiness and owner-handoff structure.

## Certified release identity

The certified and deployed release is:

- Commit: `17573fb649f74a3ba0f1b3fbc9e004108b3cf228`
- Tag: `prod-deploy-20260804-17573fb`
- Deployment run: `30944978175`

The production workflow resolved the immutable tag to the certified commit, executed the locked production migration, built and scanned the release image, deployed it to Azure, verified the allowlisted application settings, confirmed the deployed `BUILD_SHA`, passed tenant-aware integrity, passed production health, and verified release identity end to end.

## Exact-SHA repository evidence

Required exact-SHA CI was terminal with no required failed, cancelled, or pending result. The successful workflow set included:

- CI tests and checks
- backend and frontend tests
- Release Verify
- secret scanning
- CodeQL
- dependency scanning and audit
- schema governance
- Sandbox Ready Evidence Gate
- Lockdown Golden Path Gate
- CROWN Magus gate
- current-main audit evidence
- production health watch

The accepted exact-SHA regression evidence includes `4,419 passed`, `8 skipped`, and zero failures in the bounded Sandbox evidence campaign. Frontend tests and production build also passed.

## Bounded supported-role, RBAC, and tenant certification

The exact-SHA Sandbox evidence campaign passed:

- mandatory tenant-boundary tripwires;
- tenant fixture regression tests against the governed tenant keys;
- runtime golden-path checks;
- dashboard route-matrix validation;
- role-matrix proof generation;
- production-bundle route-key integrity;
- required Playwright and evidence-manifest validation.

Supported dashboard-role proof covered:

- `compliance-director`: 6 governed routes
- `crown-master`: 10 governed routes
- `deputy-head`: 10 governed routes
- `headteacher`: 10 governed routes
- `school-admin`: 10 governed routes
- `teacher`: 10 governed routes

Roles not configured as supported dashboard personas are not represented as certified active roles. No claim is made that unsupported parent, student, board, or auditor dashboards are enabled.

## Payment-processing boundary

External payment processing remains disabled and fail closed.

Exact-release tests verify that:

- unsupported external providers such as Stripe, PayPal, Square, and Adyen are rejected;
- rejected external-provider provisioning performs no tenant or provisioning-job writes;
- only `manual` and `none` are accepted tenant payment modes;
- frontend payment authority contains `PAYMENT_PROCESSING_ENABLED = false` and presents the disabled-state message.

Payment-provider selection, contracting, credentialing, transaction certification, settlement, refunds, disputes, and activation are **DEFERRED — NEW OWNER**.

## Security incident disposition

The historically exposed Ed25519 private key is treated as compromised, permanently retired, and prohibited from use. Repository evidence identified no operational trust registration or runtime dependency for that key.

A replacement key pair was generated outside the repository. Replacement public-key fingerprint:

`SHA256:LZFSVFlLCr3d1iFBB2yeLAiE2sCseSorgVvF+9Ymu70`

The replacement private key must remain outside Git and must not be uploaded to GitHub.

Git-history rewriting is **DEFERRED / NOT A RELEASE BLOCKER** unless specifically required by a buyer, insurer, auditor, counsel, or binding compliance obligation.

## Defect posture

At reconciliation time, GitHub reported no open issue carrying the `critical` label and no open issue carrying the `high` label. This is issue-tracker evidence, not a guarantee that no undiscovered defect exists.

No failed release, deployment, migration, tenant-integrity, health, identity, or payment-containment gate is currently known for the certified supported scope.

## Residual operational risks and deferred maturity work

The following are disclosed and remain outside the completed bounded technical certification unless separately executed and accepted:

- full application rollback drill and isolated operational-backup restore with measured RTO/RPO;
- exhaustive credential-class rotation and break-glass exercises;
- monitoring escalation and incident-tabletop exercises beyond the passing production health controls;
- exhaustive vendor, DPA, region, subprocessor, and jurisdiction reconciliation;
- synthetic correction, export, deletion, legal-hold, and restored-backup lifecycle exercises;
- buyer-controlled account creation, access transfer, and seller-access removal before a buyer exists;
- future payment-provider contracting and activation;
- deferred historical Git rewrite of the retired key.

These items must remain visible in diligence and handoff materials. They must not be represented as completed.

## Buyer and successor handoff

No buyer or successor has yet accepted operational turnover. The handoff package must distinguish:

- `SELLER COMPLETE`
- `NEW OWNER ACTION`
- `DEFERRED`
- `OPTIONAL MATURITY`

Final buyer acceptance, successor account creation, credential transfer, and seller-access removal occur only when a buyer is identified and the parties authorize the transfer.

## Current final status

**CERTIFIED RELEASE:** `17573fb649f74a3ba0f1b3fbc9e004108b3cf228` / `prod-deploy-20260804-17573fb`  
**REPOSITORY TECHNICAL CERTIFICATION:** PASS  
**PRODUCTION DEPLOYMENT AND RUNTIME CERTIFICATION:** PASS  
**BOUNDED ROLE / RBAC / TENANT CERTIFICATION:** PASS  
**PAYMENT PROCESSING:** DISABLED / FAIL CLOSED / DEFERRED TO NEW OWNER  
**FINAL PRODUCTION AUTHORIZATION:** PENDING FOUNDER/PRODUCT OWNER DECISION AND RESIDUAL-RISK ACCEPTANCE  
**BUYER TURNOVER:** PENDING HANDOFF RECONCILIATION AND BUYER ACCEPTANCE
