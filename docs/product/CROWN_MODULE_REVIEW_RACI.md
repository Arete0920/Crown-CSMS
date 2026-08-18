# CROWN Module Review and Certification Governance

**Status:** ACTIVE GOVERNANCE CONTROL  
**Last reconciled:** 2026-08-18  
**Parent canon:** `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`  
**Release authority:** `docs/CURRENT_RELEASE_STATUS.md` and exact current Git/GitHub repository identity  
**Operational-transfer authority:** `docs/ownership/OWNER_HANDOFF.md`

## Purpose

This document defines the review and certification governance path for CROWN modules and dashboards. It does not itself certify a module, authorize a deployment, activate payment processing, complete buyer acceptance, or substitute for the technical evidence required by the module and dashboard control matrices.

## Current governance model

CROWN is operated by a solo developer. The work author cannot represent self-review as independent review or self-approve their own work. Where an eligible independent human reviewer is available and formally engaged, independent review may be retained as additional evidence.

Where no eligible independent human reviewer is available, the approved `SOLO_DEVELOPER_APPROVED_WORKAROUND` is the governing compensating-control path. That path requires:

1. exact-head automated checks appropriate to the changed surface;
2. evidence-gated inspection of the bounded scope;
3. resolution of every actionable finding;
4. zero unresolved actionable review threads;
5. fresh ancestry and mergeability verification;
6. expected-head-SHA protection for the governed merge;
7. explicit documentation that automated assistance is not independent human approval authority; and
8. no self-approval or false independent-review claim.

This governance correction is retained in the completed issue #14 program record and supersedes older CROWN control text that made an unavailable independent human reviewer an absolute certification blocker. It does **not** weaken technical, tenant, permission, security, privacy, data-integrity, runtime, evidence, or recovery requirements.

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