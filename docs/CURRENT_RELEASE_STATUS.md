# CROWN Current Release Status

**Last reconciled:** 2026-08-08  
**Certified release decision/deployment date:** 2026-08-04  
**Repository:** `tcmegahan/Crown2026`  
**Certified release source:** `17573fb649f74a3ba0f1b3fbc9e004108b3cf228`  
**Immutable production tag:** `prod-deploy-20260804-17573fb`  
**Production deployment run:** `30944978175`  
**Development baseline reconciled by this document:** `39ab8249adf1715eb653709c0bf410535b1cad51`  
**Controlling authority:** GitHub issue `#1619`

## Identity boundary

The certified production release remains commit `17573fb649f74a3ba0f1b3fbc9e004108b3cf228` under immutable tag `prod-deploy-20260804-17573fb`.

Development `main` has advanced beyond that certified production source and includes post-certification source changes, including later UI/dashboard-integrity work and repository process hardening. This document deliberately uses `39ab8249adf1715eb653709c0bf410535b1cad51` as its development reconciliation baseline; that SHA is not asserted as a permanently current branch pointer. Later `main` commits may advance beyond it. Those later commits do **not** replace, extend, or inherit certified production status merely because they are on `main`. They require their own exact-source release selection, deployment identity, and applicable certification before the production tag or certified runtime identity can move.

Certified-production facts and development-head facts must therefore be reported separately. For the current development head after this reconciliation, consult the repository rather than treating this document's reconciliation baseline as a permanently current branch pointer.

The body of controlling issue `#1619` contains historical metadata that records repository visibility as `PUBLIC` and a prior development-main SHA. A later locked 2026-08-08 authority-correction comment on that issue supersedes those two stale metadata fields: live repository metadata was verified as `PRIVATE`, and the earlier development-main SHA is retained only as a historical baseline. The certified production source, immutable tag, deployment run, and completed release decision remain unchanged.

## Canonical decision

CROWN completed repository and production technical certification for the bounded supported release scope at the certified release identity above.

- Certified repository release technical gates: **PASS**
- Certified production deployment and runtime technical gates: **PASS**
- Certified bounded supported-role, RBAC, and tenant-isolation campaign: **PASS**
- Founder/Product Owner release authorization for the certified release: **RECORDED / ACCEPTED**
- Payment processing: **DEFERRED — NEW OWNER; DISABLED; FAIL CLOSED**
- Buyer operational turnover: **PENDING IDENTIFIED BUYER AND PARTY ACCEPTANCE**
- Post-certification development commits on `main`: **NOT PART OF THE CERTIFIED PRODUCTION IDENTITY UNLESS SEPARATELY RELEASED AND CERTIFIED**

This document records the evidence-backed posture and deliberately distinguishes certified production from later development activity. GitHub issue `#1619` remains the controlling record for the certified release and owner-handoff boundary, subject to its later explicit correction comments where the issue body contains superseded metadata.

## Certified release identity

The certified and deployed release is:

- Commit: `17573fb649f74a3ba0f1b3fbc9e004108b3cf228`
- Tag: `prod-deploy-20260804-17573fb`
- Deployment run: `30944978175`

The production workflow resolved the immutable tag to the certified commit, executed the locked production migration, built and scanned the release image, deployed it to Azure, verified the allowlisted application settings, confirmed the deployed `BUILD_SHA`, passed tenant-aware integrity, passed production health, and verified release identity end to end.

## Exact-SHA repository evidence for the certified release

Required exact-SHA CI was terminal with no required failed, cancelled, or pending result. The successful workflow set included:

- CI tests and checks
- backend and frontend tests
- Release Verify
- secret scanning
- CodeQL
- dependency scanning and audit
- schema governance
- bounded sandbox evidence gate
- Lockdown Golden Path Gate
- CROWN Magus gate
- current-main audit evidence at certification time
- production health watch

The accepted exact-SHA regression evidence includes `4,419 passed`, `8 skipped`, and zero failures in the bounded sandbox evidence campaign. Frontend tests and production build also passed.

## Bounded supported-role, RBAC, and tenant certification

The certified exact-SHA sandbox evidence campaign passed:

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

Roles not configured as supported dashboard personas are not represented as certified active roles. No claim is made that unsupported parent, student, board, or auditor dashboards are enabled in the certified release.

## Post-certification development state

For this authority reconciliation, `39ab8249adf1715eb653709c0bf410535b1cad51` is the selected development baseline used to distinguish later source state from the certified production identity. It is not presented as a permanently current `main` pointer or as a replacement for historical branch-verification metadata in #1619. The baseline contains later source changes after the certified release, including visual-layout, display-integrity, sandbox-layout, cross-layer dashboard-integrity, legacy operational-dashboard work, and PR/visual-system preflight hardening.

Later development changes may have their own exact-head CI and review evidence, but they are not represented by this document as deployed production changes. The immutable certified tag remains the only certified production identity until a later source is explicitly selected, tagged, deployed, identity-reconciled, and certified.

## Payment-processing boundary

External payment processing remains disabled and fail closed for the certified release.

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

At certified-release reconciliation time, GitHub reported no open issue carrying the `critical` label and no open issue carrying the `high` label. That is issue-tracker evidence at that point in time, not a continuing guarantee and not a guarantee that no undiscovered defect exists.

No failed release, deployment, migration, tenant-integrity, health, identity, or payment-containment gate is recorded for the certified supported scope.

Later development work must be assessed on its own current evidence and must not inherit this statement automatically.

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

The handoff package for the certified release is ready for buyer diligence and transaction-specific transfer. Actual buyer turnover remains pending until a buyer is identified and the parties complete acceptance, successor account creation, credential transfer, and seller-access removal.

The handoff package must distinguish:

- `SELLER COMPLETE`
- `NEW OWNER ACTION`
- `DEFERRED`
- `OPTIONAL MATURITY`

## Current final status

**CERTIFIED PRODUCTION RELEASE:** `17573fb649f74a3ba0f1b3fbc9e004108b3cf228` / `prod-deploy-20260804-17573fb`  
**DEVELOPMENT BASELINE RECONCILED BY THIS DOCUMENT:** `39ab8249adf1715eb653709c0bf410535b1cad51`  
**CURRENT DEVELOPMENT HEAD:** CONSULT REPOSITORY; DO NOT INFER PRODUCTION CERTIFICATION FROM `main`  
**CERTIFIED RELEASE REPOSITORY TECHNICAL CERTIFICATION:** PASS / COMPLETE  
**CERTIFIED RELEASE PRODUCTION DEPLOYMENT AND RUNTIME CERTIFICATION:** PASS / COMPLETE  
**CERTIFIED RELEASE BOUNDED ROLE / RBAC / TENANT CERTIFICATION:** PASS / COMPLETE  
**FOUNDER/PRODUCT OWNER RELEASE AUTHORIZATION FOR CERTIFIED RELEASE:** RECORDED / ACCEPTED  
**POST-CERTIFICATION MAIN CHANGES:** NOT INCLUDED IN CERTIFIED PRODUCTION IDENTITY UNTIL SEPARATELY RELEASED AND CERTIFIED  
**PAYMENT PROCESSING:** DISABLED / FAIL CLOSED / DEFERRED TO NEW OWNER  
**HANDOFF PACKAGE:** READY FOR BUYER DILIGENCE AND TRANSACTION-SPECIFIC TRANSFER OF THE CERTIFIED RELEASE  
**ACTUAL BUYER TURNOVER:** PENDING IDENTIFIED BUYER AND PARTY ACCEPTANCE
