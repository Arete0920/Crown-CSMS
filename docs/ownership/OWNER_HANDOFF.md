# CROWN Owner Handoff

**Status:** Canonical transfer guide — current release certification pending\
**Release-claim reconciliation:** 2026-10-22\
**Authority:** `docs/CURRENT_RELEASE_STATUS.md`

## Current posture

CROWN is currently a release candidate, not a certified current production deployment. The August 18, 2026 engineering certification covers its historical baseline; it does not certify the current `main` after subsequent security, dependency, and architecture changes. Under `docs/CURRENT_RELEASE_STATUS.md`, the selected exact source head requires applicable repository/security checks, and deployment, recovery, payment, and buyer acceptance require separate operational evidence.

Owner transfer remains a separate transaction-time process. Historical engineering certification is not a substitute for successor deployment/runtime identity, operational recovery evidence, successor-controlled account ownership, credential transition, payment-provider activation, or final buyer acceptance.

## Required transfer sequence

1. Verify the exact Crown-CSMS `main` SHA, review `docs/CURRENT_RELEASE_STATUS.md`, and obtain release evidence applicable to that exact head; do not infer current certification from the August 18 historical record.
2. Verify that no required transfer work is stranded only on a non-main branch.
3. Confirm the signed transaction/transfer authority, effective date, successor entity, and authorized successor representatives.
4. Establish one exact source, deployment, and runtime identity with false-positive-resistant evidence.
5. Establish successor-controlled repository, cloud, domain, certificate, monitoring, backup, vendor, billing, and recovery accounts before seller access is removed.
6. Configure and verify production monitoring, escalation, and the approved runtime-health path under successor ownership.
7. Execute or explicitly disposition the immutable application rollback drill against the selected production identity.
8. Execute or explicitly disposition operational backup/restore proof, including measured RTO/RPO where required.
9. Rotate credentials and recovery factors; verify recovery and revoke prior access in the contractually approved sequence.
10. Verify clean-clone setup, deployment, monitoring, rollback/restore procedures, and required operational exercises.
11. Update repository rules, approvers, contacts, notifications, and ownership controls for the successor.
12. Complete provider-specific payment certification only after provider contract, merchant credentials, transaction/webhook/settlement/refund/dispute/reconciliation proof, and applicable qualified review.
13. Record final buyer acceptance, exceptions, qualified reviews, residual risks, and seller-access removal.

## Pre-contract versus post-contract boundary

Before signed transaction authority, repository/product engineering may be maintained and defects may be corrected, but buyer-specific production ownership, credentials, seller-access removal, monitoring ownership, production identity, and acceptance must not be executed prematurely.

After signed authority, use the operational-transfer register and the post-contract GitHub transfer checklist as the execution control for successor-specific actions.

## Transfer claim boundary

Documentation cleanliness, production-ready engineering certification, production deployment, operational recovery acceptance, payment-provider activation, legal/transaction review, and completed owner turnover are separate claims.

A handoff is complete only when the successor can independently operate, recover, secure, and govern the exact transferred system and the transfer record identifies accepted residual risks without ambiguity.
