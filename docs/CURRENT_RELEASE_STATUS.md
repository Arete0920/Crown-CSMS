# CROWN Current Release Status

**Status:** Canonical release, freeze, and turnover authority  
**Last verified:** 2026-08-17  
**Repository:** `Arete-Advisory-Group/Crown-CSMS`

## Exact source authority

The exact GitHub `main` commit being handed off is the current Crown-CSMS source identity. Historical PR heads, program-start SHAs, migration baselines, Crown2026 tags, and prior certification runs are provenance only and must not be described as current `main`.

Any change to `main` invalidates prior exact-head certification. Final handoff must therefore resolve the current `main` SHA and verify required checks against that same identity.

## Current decision boundary

Repository turnover, production deployment, buyer acceptance, and payment activation are separate decisions.

- Repository turnover readiness: determined from terminal exact-main repository/security/tenant/runtime evidence for the commit handed off.
- Production deployment/runtime identity: **NOT ESTABLISHED BY REPOSITORY EVIDENCE ALONE**; require source-to-build-to-deployment-to-runtime proof.
- Owner acceptance and account transfer: require successor-controlled transfer steps in `docs/ownership/OWNER_HANDOFF.md`.
- Payment processing: **DISABLED / FAIL CLOSED / NOT AUTHORIZED FOR ACTIVATION** pending provider selection, contracts, credentials, transaction certification, and explicit authorization.

## Historical predecessor evidence

Crown2026 is preserved as historical predecessor/provenance/rollback evidence. Crown2026 issue #1619 and predecessor release artifacts do not control Crown-CSMS execution or release claims.

## Current successor authority

Crown-CSMS issue #14 is the execution-control record for final reconciliation, exact successor proof, canonical authority refresh, and owner turnover. Closed domain issues and merged PRs remain evidence for bounded changes; open issues must be classified as release-blocking, accepted residual, or post-handoff improvement work rather than silently ignored.

## Required handoff gates

1. Reconcile current-main P0 security, tenant, authorization, and data-integrity defects.
2. Keep one authoritative mutation path per domain and remove or explicitly retire competing active authorities.
3. Reconcile surviving branches/issues so historical residue is not mistaken for unfinished production work.
4. Keep canonical owner-facing documents current and noncontradictory.
5. Freeze one exact `main` SHA and require terminal required checks on that same SHA.
6. Verify repository/security/tenant/RBAC/schema/dependency/runtime evidence proportional to release risk.
7. Verify rollback/recovery procedures and identify deployment/runtime state truthfully.
8. Transfer successor-controlled repository/cloud/domain/certificate/monitoring/backup/vendor/billing access, rotate recovery factors and credentials, and record acceptance outside source-code certification as applicable.

## Disposition

- Crown-CSMS active successor repository: **CURRENT**
- Crown2026 predecessor: **HISTORICAL / PRESERVED**
- Exact repository source identity: **CURRENT GITHUB `main` SHA**
- Production deployment/runtime identity: **VERIFY SEPARATELY**
- Payment processing: **DISABLED / FAIL CLOSED**
- Owner turnover: **COMPLETE ONLY WHEN THE TRANSFER SEQUENCE AND SUCCESSOR ACCEPTANCE ARE RECORDED**
