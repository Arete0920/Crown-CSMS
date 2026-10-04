# CROWN Module Review and Certification Governance

**Status:** ACTIVE GOVERNANCE CONTROL  
**Last reconciled:** 2026-08-18  
**Parent canon:** `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`  
**Release authority:** `docs/CURRENT_RELEASE_STATUS.md` and exact current Git/GitHub repository identity  
**Operational-transfer authority:** `docs/ownership/OWNER_HANDOFF.md`

## Purpose

This document defines the review and certification governance path for CROWN modules and dashboards and retains the canonical 53-row review inventory required by repository integrity controls. It does not itself certify a module, authorize a deployment, activate payment processing, complete buyer acceptance, or substitute for technical evidence.

## Current governance model

CROWN is operated by a solo developer. The work author cannot represent self-review as independent review or self-approve their own work. Where an eligible independent human reviewer is available and formally engaged, independent review may be retained as additional evidence.

Where no eligible independent human reviewer is available, the approved `SOLO_DEVELOPER_APPROVED_WORKAROUND` is the governing compensating-control path. That path requires:

1. exact-head automated checks appropriate to the changed surface;
2. evidence-gated inspection of the bounded scope;
3. resolution of every actionable finding;
4. zero unresolved actionable review threads;
5. fresh ancestry and mergeability verification;
6. expected-head-SHA protection for the governed merge;
7. explicit documentation that **repository tooling and automated checks are not approval authority**; and
8. no self-approval or false independent-review claim.

The completed issue #14 governance record documents this approved path and supersedes older CROWN control text that made an unavailable independent human reviewer an absolute certification blocker. This does **not** weaken technical, tenant, permission, security, privacy, data-integrity, runtime, evidence, or recovery requirements.

## Roles

| Responsibility | Current governance assignment |
|---|---|
| Product and scope accountability | Founder / Product Owner |
| Work author | PR / commit author for the bounded change |
| Technical evidence | Exact-head repository tests, runtime proof, evidence artifacts, and applicable security/quality gates |
| Review path | Independent human review when available; otherwise `SOLO_DEVELOPER_APPROVED_WORKAROUND` |
| Security/privacy evidence | Required technical controls and evidence for sensitive surfaces; qualified external review only where a separate legal, contractual, regulatory, buyer, or governing-party requirement requires it |
| Release authority | Current repository release controls; never inferred from this document alone |
| Operational-transfer acceptance | Authorized successor/buyer parties under `docs/ownership/OWNER_HANDOFF.md` |

## Certification rule

A module or dashboard may be marked `Certified` only when its required technical and functional evidence is current and tied to the exact source identity being certified. The absence of an independent human reviewer is **not**, by itself, a blocker when the approved solo-developer compensating-control path has been completed and recorded.

Certification still requires, as applicable:

- canonical domain ownership and lifecycle behavior;
- schema/model/service/API wiring;
- tenant isolation and cross-tenant negative proof;
- entitlement and action-level permission enforcement;
- validation, error, transaction, and audit behavior;
- frontend workflow and direct-route behavior;
- dashboard live/snapshot provenance and freshness;
- sensitivity, redaction, and export behavior;
- backend/frontend/runtime tests;
- browser or other runtime evidence where the control matrix requires it;
- exact-source evidence linkage;
- all actionable findings resolved; and
- the approved governance review path recorded.

Registry presence, page rendering, sample data, fallback data, historical evidence, or a green build by itself is not certification.

## Canonical review inventory

Every row below uses the same review rule: independent human review when an eligible reviewer is available; otherwise the approved `SOLO_DEVELOPER_APPROVED_WORKAROUND`. `Security/Privacy` indicates whether enhanced security/privacy evidence is required for the row. It does not create an unavailable-human-review blocker.

| Phase | Module Key | Review Path | Security/Privacy |
|---|---|---|---|
| 0 | `tenant-school-context` | Approved governance path | REQUIRED |
| 0 | `identity-users-roles` | Approved governance path | REQUIRED |
| 0 | `rbac-permissions` | Approved governance path | REQUIRED |
| 0 | `audit-logging` | Approved governance path | REQUIRED |
| 0 | `entitlements-subscriptions` | Approved governance path | REQUIRED |
| 0 | `retention-rollover` | Approved governance path | REQUIRED |
| 0 | `dashboard-certification-contract` | Approved governance path | REQUIRED |
| 1 | `school-year-grade` | Approved governance path | AS REQUIRED |
| 1 | `staff-user-role` | Approved governance path | REQUIRED |
| 1 | `family-guardian-household` | Approved governance path | REQUIRED |
| 1 | `student-master` | Approved governance path | REQUIRED |
| 1 | `enrollment-registrar` | Approved governance path | REQUIRED |
| 1 | `courses-sections-rosters` | Approved governance path | AS REQUIRED |
| 1 | `attendance` | Approved governance path | REQUIRED |
| 1 | `gradebook` | Approved governance path | REQUIRED |
| 1 | `transcripts-reportcards` | Approved governance path | REQUIRED |
| 1 | `student-care-discipline` | Approved governance path | REQUIRED |
| 2 | `admissions` | Approved governance path | REQUIRED |
| 2 | `re-enrollment` | Approved governance path | REQUIRED |
| 2 | `billing-tuition-ledger` | Approved governance path | REQUIRED |
| 2 | `financial-aid` | Approved governance path | REQUIRED |
| 2 | `communications` | Approved governance path | REQUIRED |
| 2 | `parent-family-portal` | Approved governance path | REQUIRED |
| 2 | `teacher-portal` | Approved governance path | REQUIRED |
| 2 | `administrator-portal` | Approved governance path | REQUIRED |
| 3 | `scheduling` | Approved governance path | AS REQUIRED |
| 3 | `activities-athletics` | Approved governance path | REQUIRED |
| 3 | `health-office` | Approved governance path | REQUIRED |
| 3 | `transportation` | Approved governance path | REQUIRED |
| 3 | `food-service` | Approved governance path | REQUIRED |
| 3 | `facilities` | Approved governance path | AS REQUIRED |
| 3 | `safety-security` | Approved governance path | REQUIRED |
| 3 | `hr` | Approved governance path | REQUIRED |
| 3 | `it-support` | Approved governance path | REQUIRED |
| 4 | `fine-arts` | Approved governance path | AS REQUIRED |
| 4 | `library-media` | Approved governance path | REQUIRED |
| 4 | `extended-care` | Approved governance path | REQUIRED |
| 4 | `summer-camp` | Approved governance path | REQUIRED |
| 4 | `spiritual-life` | Approved governance path | REQUIRED |
| 4 | `service-outreach-portrait` | Approved governance path | REQUIRED |
| 4 | `volunteer-management` | Approved governance path | REQUIRED |
| 4 | `advancement-operations` | Approved governance path | REQUIRED |
| 4 | `alumni-relations` | Approved governance path | REQUIRED |
| 4 | `board-governance` | Approved governance path | REQUIRED |
| 4 | `curriculum-pd` | Approved governance path | AS REQUIRED |
| 4 | `network-benchmarking` | Approved governance path | REQUIRED |
| 5 | `implementation-success` | Approved governance path | AS REQUIRED |
| 5 | `data-migration` | Approved governance path | REQUIRED |
| 5 | `integrations-automation` | Approved governance path | REQUIRED |
| 5 | `compliance-audit` | Approved governance path | REQUIRED |
| 5 | `revenue-operations` | Approved governance path | REQUIRED |
| 5 | `release-reliability` | Approved governance path | AS REQUIRED |
| 5 | `dashboard-certification-center` | Approved governance path | AS REQUIRED |

## Evidence record

For every certification promotion, retain enough evidence to identify:

1. module or dashboard key;
2. exact source SHA;
3. bounded scope certified;
4. data-ownership and lifecycle evidence;
5. permission and tenant evidence;
6. API/service/error/audit evidence;
7. frontend/direct-route evidence;
8. dashboard provenance/freshness evidence where applicable;
9. exact tests and runtime artifacts;
10. findings and their disposition;
11. governance path used: independent review or `SOLO_DEVELOPER_APPROVED_WORKAROUND`;
12. unresolved risks or explicit statement that required findings are resolved.

If the solo-developer path is used, the evidence must say so directly and must not label the result as independent human approval.

## Relationship to older module controls

The technical status rows in the existing module/dashboard matrices remain conservative until exact evidence supports promotion. This document changes **governance semantics only**; it does not mass-promote any row.

For governance interpretation:

- older references to GitHub issue `#1619` are historical predecessor-era authority and are not current Crown-CSMS release authority;
- older statements that `UNASSIGNED` independent human review automatically blocks certification are superseded by this current control when the approved solo-developer workaround is used;
- `docs/CURRENT_RELEASE_STATUS.md` remains the repository/release authority;
- transaction-time owner/buyer transfer remains separate from repository certification.

## Claim boundary

This control does not claim independent human review, legal or regulatory certification, production deployment, buyer acceptance, payment-provider authorization, or operational account transfer. Those claims require their own evidence and authority.