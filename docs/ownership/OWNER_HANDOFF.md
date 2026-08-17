# CROWN Owner Handoff

**Status:** Canonical transfer guide  
**Last verified:** 2026-08-17  
**Authority:** `docs/CURRENT_RELEASE_STATUS.md`

## Current posture

Crown-CSMS is the active successor engineering and owner-turnover repository. The exact GitHub `main` commit being transferred is the source identity. Historical PR heads, Crown2026 release records, and predecessor issue #1619 are provenance only and do not control the current repository.

Repository certification and operational ownership transfer are separate gates. Payment processing remains disabled and fail closed until separately authorized.

## Required transfer sequence

1. Resolve and record the exact Crown-CSMS `main` SHA being transferred.
2. Verify required exact-main repository, security, tenant, RBAC, schema, dependency, and runtime checks are terminal for that same SHA; record any accepted residuals explicitly.
3. Review the canonical and diligence indexes and ensure no owner-facing authority cites a stale SHA as current.
4. Confirm production deployment/runtime identity separately from repository identity; if no production deployment is established, state that plainly.
5. Review open issues and surviving branches; distinguish active blockers from historical residue and post-handoff improvement work.
6. Confirm rollback/recovery procedures and the source identity to which the repository can be reverted.
7. Identify the successor and obtain acceptance of exact scope, limitations, residual risks, and current deployment/payment state.
8. Establish successor-controlled repository, cloud, domain, certificate, monitoring, backup, vendor, contract, and billing access before seller access is removed.
9. Rotate credentials and recovery factors under the successor's control; verify recovery and revoke prior access.
10. Verify clean-clone setup and, where operational infrastructure is in scope, deployment, monitoring, rollback, and restore exercises.
11. Update repository rules, owners, approvers, contacts, alerts, and notifications to successor-controlled identities.
12. Record final acceptance, exceptions, qualified reviews, residual risks, and seller-access removal.

## Handoff evidence rule

The source repository may record technical evidence and procedures, but secrets, recovery codes, private certificates, production data, personal credentials, and confidential buyer records must not be committed. Account-transfer and credential-rotation proof should be recorded in the approved secure handoff channel.

Documentation cleanliness, repository certification, production authorization, buyer diligence readiness, and operational turnover are separate gates. Legal, tax, accounting, transaction, valuation, contractual, insurance, privacy, accessibility, security, and payment-provider conclusions require appropriate qualified review.
