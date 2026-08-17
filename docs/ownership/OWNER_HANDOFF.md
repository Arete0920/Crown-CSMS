# CROWN Owner Handoff

**Status:** Canonical transfer guide  
**Last verified:** 2026-08-17  
**Authority:** `docs/CURRENT_RELEASE_STATUS.md`

## Current posture

Crown-CSMS is the active successor engineering and owner-turnover repository. The current handoff-refresh branch is based on `main` at `f9bf6b4143e707f93ec8d6ce319327ddc7d3e2a0`, after merged security-hardening PRs #97 and #98.

Repository evidence is not a substitute for deployment/runtime identity, recovery evidence, successor account control, or final acceptance. Crown2026 is historical predecessor/provenance evidence only. Payment processing remains disabled and fail closed.

## Required transfer sequence

1. Verify the exact Crown-CSMS `main` SHA and current release status.
2. Verify that no required production work is stranded only on a non-main branch.
3. Review the canonical and diligence indexes and remove stale or competing authority.
4. Confirm zero unresolved release-blocking P0 defects; classify remaining issues accurately as roadmap, architecture follow-up, external dependency, or nonblocking technical debt.
5. Establish one exact source, deployment, and runtime identity with false-positive-resistant evidence.
6. Verify monitoring and the approved runtime-health path.
7. Execute or explicitly disposition the immutable application rollback drill against the selected release identity.
8. Execute or explicitly disposition operational backup/restore proof, including measured RTO/RPO where required.
9. Record the approved solo-developer governance workaround accurately; do not represent automated review or self-review as independent human approval.
10. Identify the successor and obtain acceptance of exact scope, limitations, and residual risks.
11. Establish successor-controlled repository, cloud, domain, certificate, monitoring, backup, vendor, and billing accounts before seller access is removed.
12. Rotate credentials and recovery factors; verify recovery and revoke prior access.
13. Verify clean-clone setup, deployment, monitoring, rollback/restore procedures, and required operational exercises.
14. Update repository rules, approvers, contacts, notifications, and ownership controls for the successor.
15. Record final acceptance, exceptions, qualified reviews, residual risks, and seller-access removal.

## Transfer claim boundary

Documentation cleanliness, repository certification, production authorization, buyer diligence readiness, recovery readiness, and operational turnover are separate gates. Legal, tax, accounting, transaction, valuation, contractual, insurance, privacy, accessibility, security, and payment-provider conclusions require appropriate qualified review where applicable.

A handoff is complete only when the successor can independently operate, recover, secure, and govern the exact transferred system and the transfer record identifies any accepted residual risks without ambiguity.
