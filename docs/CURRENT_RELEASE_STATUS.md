# CROWN Current Release Status

**Status:** Canonical repository/release authority  
**Last verified:** 2026-08-18  
**Current repository identity:** resolve exact `refs/heads/main` from Git/GitHub at the decision point; do not copy a mutable SHA into this file  
**Migration baseline:** `ac574ab2a55ecbfefb40cbd67bad08d99c085575`

## Identity rule

This document intentionally does **not** embed the SHA of its own `main` commit as a durable current-status field. A mutable authority record cannot truthfully predict the merge SHA that will contain it.

For every certification, transfer, release, deployment, rollback, or diligence decision that requires exact identity:

1. resolve the current `refs/heads/main` SHA directly from Git/GitHub at the decision point;
2. record that exact SHA in the immutable evidence packet, release/transfer record, workflow result, or signed transaction artifact for that decision;
3. verify ancestry and required checks for that exact SHA or its certified PR head as applicable; and
4. never substitute an older SHA copied from mutable documentation.

## Current decision

The predecessor-to-Crown-CSMS migration and successor engineering gap-closure program tracked by issue #14 is **COMPLETED**. The repository authority/hygiene/security closure sequence through PR #112 is also completed and merged. PR #112 closed the verified public DEV/demo ops fail-open seam outside authorized DEV/test runtimes and simplified the required pytest gate so the required check is owned by the actual pytest execution job.

PR #112 was locally exact-head certified at `915bf224bf714f5b5f4f31eb5745971af813f2e4`, merged as `1122b73d4072d8b98b311ffcca07d019bbcae1e8`, and the temporary PR-only OrganizationAdmin ruleset bypass used for that governed merge was removed immediately afterward. `main-protection` returned to active enforcement with no bypass actors.

Repository engineering completion is distinct from transaction-time operational transfer. **No successor production deployment, production tag, payment activation, buyer acceptance, or operational turnover is asserted by this record.**

## Current repository state

- Crown-CSMS active successor repository: **VERIFIED**
- Exact current repository source: **resolve current `refs/heads/main` from Git/GitHub**
- Migration/successor engineering gap-closure issue #14: **CLOSED / COMPLETED / HISTORICAL PROGRAM RECORD**
- Repository authority/hygiene reconciliation through PR #111: **COMPLETED / MERGED**
- PR #112 DEV/demo ops fail-closed security repair and pytest-gate reliability repair: **MERGED / EXACT-HEAD LOCALLY CERTIFIED / GOVERNANCE RESTORED**
- Student Records #66: **CLOSED / COMPLETED**
- HR #67: **CLOSED / RELEASE-CRITICAL SECURITY REPAIR COMPLETED**
- Transportation P0 #78: **CLOSED / COMPLETED**
- Spiritual Life P0 #82: **CLOSED / COMPLETED**
- Athletics P0 #65: **CLOSED / COMPLETED**
- Student Care P0 #64: **CLOSED / COMPLETED**
- Little Lambs #81: **CLOSED / NOT PLANNED FOR CURRENT CROWN HANDOFF SCOPE**
- Communications #63: **ROADMAP / CUSTOMER-TENANT MICROSOFT 365 AND DELIVERY AUTHORITY**
- Microsoft Education integration #68: **ROADMAP / POST-HANDOFF CUSTOMER INTEGRATION**
- CI cost #74: **POST-HANDOFF OPTIMIZATION / NOT A CURRENT APPLICATION DEFECT BY ITSELF**

## Module and dashboard certification boundary

The product control matrices remain conservative row-level certification controls. `Inventory`, `Scaffold`, `Hybrid`, or `Live` matrix states do not by themselves mean a product capability is absent; they mean the matrix-specific certification evidence required for a `Certified` promotion has not been completed for that row.

Certification governance is controlled by `docs/product/CROWN_MODULE_REVIEW_RACI.md`. The work author may not self-review or self-approve. When an eligible independent human reviewer is unavailable, the approved `SOLO_DEVELOPER_APPROVED_WORKAROUND` is the governing compensating-control path. Automated assistance is not approval authority.

## Operational evidence boundary

Repository certification and transaction-time production-operation proof are separate claims.

Current repository runbooks establish executable rollback/restore mechanics and historical/mechanics evidence. The following transaction-time or environment-specific items do **not** reopen the completed engineering program and must be completed or explicitly accepted by authorized parties when an actual successor transfer/release is selected:

1. exact selected repository/release SHA and, where applicable, exact deployed runtime identity;
2. authorized immutable rollback execution evidence against that identity;
3. operational backup/restore evidence tied to that selected identity, including measured RTO/RPO where required;
4. monitoring and recovery evidence appropriate to the target owner/environment;
5. successor-controlled accounts, credential/recovery-factor rotation, and seller-access removal; and
6. successor acceptance of scope, limitations, and residual risks.

**Buyer operational turnover: PENDING IDENTIFIED BUYER AND PARTY ACCEPTANCE**

## Historical predecessor evidence

The predecessor repository, predecessor release campaigns, obsolete issue/PR authority references, and completed issue-program records are historical provenance evidence only. They are not current Crown-CSMS execution, release, deployment, recovery, certification, or turnover authority unless a current canonical record explicitly incorporates a bounded fact.

## Payment boundary

**PAYMENT PROCESSING: DISABLED / FAIL CLOSED / NOT AUTHORIZED FOR ACTIVATION**

Provider selection, contracting, credentials, transaction certification, settlement, refunds, disputes, legal, tax, accounting, and payment-provider conclusions require separate authorization and qualified review.

## Claim boundary

Do not claim that Crown-CSMS is production deployed, operationally transferred, payment ready, legally certified, regulator approved, or independently human reviewed unless current exact evidence and the appropriate authority establish that claim.

## Completion and transfer authority

Issue #14 is a **completed historical engineering-program record**, not active execution authority. Current repository release posture is governed by this document, exact Git/GitHub identity, and the current canonical documentation index. Module/dashboard certification governance is governed by `docs/product/CROWN_MODULE_REVIEW_RACI.md`. Transaction-time successor acceptance and account-transfer actions are governed by the current owner-handoff/operational-transfer records and authorized parties.
