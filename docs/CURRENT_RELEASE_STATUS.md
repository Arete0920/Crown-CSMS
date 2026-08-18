# CROWN Current Release Status

**Status:** Canonical repository/release authority  
**Last verified:** 2026-08-18  
**Current repository identity:** exact `refs/heads/main` at the time this record is used; resolve it from Git/GitHub rather than copying a self-invalidating mutable SHA into this file  
**Migration baseline:** `ac574ab2a55ecbfefb40cbd67bad08d99c085575`

## Identity rule

This document intentionally does **not** embed the SHA of its own `main` commit as a durable current-status field. A file committed to `main` cannot truthfully name the resulting merge SHA before that merge exists; doing so causes the authority record to lag by one commit indefinitely.

For every certification, transfer, release, deployment, rollback, or diligence decision that requires exact identity:

1. resolve the current `refs/heads/main` SHA directly from Git/GitHub at the decision point;
2. record that exact SHA in the immutable evidence packet, release/transfer record, workflow result, or signed transaction artifact for that decision;
3. verify ancestry and required checks for that exact SHA or its certified PR head as applicable;
4. never substitute an older SHA copied from a mutable documentation file.

## Current decision

The predecessor-to-Crown-CSMS migration and successor engineering gap-closure program tracked by issue #14 is **COMPLETED**. Current successor `main` includes the owner-turnover/canonical reconciliation sequence through PR #108, including Student Records defense-in-depth authorization repair, owner-handoff authority/certification-plumbing reconciliation, retirement of obsolete May-era release-authority controls, post-retirement authority cleanup, and canonical handoff-base reconciliation.

Repository engineering completion is distinct from transaction-time operational transfer. **No successor production tag or release is asserted by this record, and buyer operational turnover remains pending an identified buyer and authorized party acceptance.**

## Current repository state

- Crown-CSMS active successor repository: **VERIFIED**
- Exact current repository source: **resolve current `refs/heads/main` from Git/GitHub**
- Migration/successor engineering gap-closure issue #14: **CLOSED / COMPLETED / HISTORICAL PROGRAM RECORD**
- PR #99 owner-turnover/canonical documentation refresh: **MERGED**
- PR #100 final architecture/hygiene reconciliation: **MERGED**
- PR #101 Student Records registrar-authority defense-in-depth: **MERGED / EXACT-HEAD CERTIFIED**
- PR #103 owner-handoff authority and final certification plumbing: **MERGED / EXACT-HEAD CERTIFIED**
- PR #105 post-#103 owner-facing authority reconciliation: **MERGED / EXACT-HEAD CERTIFIED**
- PR #106 obsolete May release-authority control retirement: **MERGED / EXACT-HEAD CERTIFIED**
- PR #107 post-retirement authority cleanup: **MERGED / EXACT-HEAD CERTIFIED**
- PR #108 canonical handoff-base reconciliation: **MERGED / EXACT-HEAD CERTIFIED**
- Student Records #66: **CLOSED / COMPLETED**
- HR #67: **CLOSED / RELEASE-CRITICAL SECURITY REPAIR COMPLETED**
- Transportation P0 #78: **CLOSED / COMPLETED**
- Spiritual Life P0 #82: **CLOSED / COMPLETED**
- Athletics P0 #65: **CLOSED / COMPLETED**
- Student Care P0 #64: **CLOSED / COMPLETED**
- Little Lambs #81: **CLOSED / NOT PLANNED FOR CURRENT CROWN HANDOFF SCOPE**
- Communications #63: **ROADMAP / CUSTOMER-TENANT MICROSOFT 365 AND DELIVERY AUTHORITY**
- Microsoft Education integration #68: **ROADMAP / POST-HANDOFF CUSTOMER INTEGRATION**
- CI cost #74: **POST-HANDOFF OPTIMIZATION**

## Operational evidence boundary

Repository certification and transaction-time production-operation proof are separate claims.

Current repository runbooks establish:

- executable immutable application rollback mechanics;
- executable isolated PostgreSQL restore mechanics;
- historical/mechanics evidence for restore behavior.

The following transaction-time or environment-specific items do **not** reopen the completed engineering program and must be completed or explicitly accepted by the authorized parties when an actual successor transfer/release is selected:

1. exact selected repository/release SHA and, where applicable, exact deployed runtime identity;
2. authorized immutable rollback execution evidence against that identity;
3. operational backup/restore evidence tied to that selected identity, including measured RTO/RPO where required;
4. monitoring and recovery evidence appropriate to the target owner/environment;
5. successor-controlled accounts, credential/recovery-factor rotation, and seller-access removal;
6. successor acceptance of scope, limitations, and residual risks.

**Buyer operational turnover: PENDING IDENTIFIED BUYER AND PARTY ACCEPTANCE**

## Historical predecessor evidence

The predecessor repository, predecessor release campaigns, and completed issue-program records are historical provenance evidence only. They are not current Crown-CSMS execution, release, deployment, recovery, or turnover authority unless a current canonical record explicitly incorporates a bounded fact.

## Payment boundary

**PAYMENT PROCESSING: DISABLED / FAIL CLOSED / NOT AUTHORIZED FOR ACTIVATION**

Provider selection, contracting, credentials, transaction certification, settlement, refunds, disputes, legal, tax, accounting, and payment-provider conclusions require separate authorization and qualified review.

## Claim boundary

Do not claim that Crown-CSMS is production deployed, operationally transferred, payment ready, legally certified, regulator approved, or independently human reviewed unless current exact evidence and the appropriate authority establish that claim.

## Completion and transfer authority

Issue #14 is a **completed historical engineering-program record**, not active execution authority. Current release, payment, recovery, and turnover posture is governed by this document and the canonical documentation index. Transaction-time successor acceptance and account-transfer actions are governed by the current owner-handoff/operational-transfer records and the authorized parties.
