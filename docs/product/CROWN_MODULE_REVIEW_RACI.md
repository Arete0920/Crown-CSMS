# CROWN Module Review RACI

Status: Planning Control Matrix
Parent Canon: `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`
Release Authority: `docs/CURRENT_RELEASE_STATUS.md`

## Purpose

This document defines review and approval responsibilities for CROWN module and dashboard completion. It exists to prevent self-approval, unclear ownership, premature certification, and unsupported release claims.

TC may set direction, priorities, and product intent, but TC cannot independently review or approve TC's own work. Any module or dashboard certification requires independent review.

## Authority Hierarchy

| Document | Controls |
|---|---|
| `docs/CURRENT_RELEASE_STATUS.md` | Repository release posture, GO/NO-GO, release freeze, current-head evidence authority. |
| `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md` | Module/dashboard product architecture, order, vocabulary, certification prerequisites. |
| `docs/product/CROWN_MODULE_COMPLETION_MATRIX.md` | Row-level module status and evidence requirements. |
| `docs/product/CROWN_MODULE_DATA_OWNERSHIP_MATRIX.md` | Canonical data ownership and duplicate-truth prevention. |
| `docs/product/CROWN_MODULE_PERMISSION_MATRIX.md` | Action-level permission and security requirements. |
| `docs/product/CROWN_DASHBOARD_FIT_MATRIX.md` | Dashboard-to-module fit and certification requirements. |
| `docs/product/CROWN_MODULE_REVIEW_RACI.md` | Independent review and approval routing. |

This file does not approve production release.

## RACI Definitions

| Code | Meaning |
|---|---|
| R | Responsible: does the work or prepares the evidence. |
| A | Accountable: owns final decision for that stage. |
| C | Consulted: provides subject-matter input. |
| I | Informed: receives status but does not approve. |

## Role Definitions

| Role | Description |
|---|---|
| Product Direction Owner | Defines priority, product intent, market fit, and module scope. TC may hold this role. |
| Implementer | Writes code, docs, tests, or evidence. Cannot self-approve. |
| Technical Reviewer | Reviews architecture, code structure, data ownership, API shape, and integration risk. |
| Security Reviewer | Reviews tenant isolation, permissions, sensitive data, redaction, exports, and auditability. |
| QA / Evidence Reviewer | Reviews tests, runtime proof, screenshots, Playwright artifacts, and evidence completeness. |
| Product Workflow Reviewer | Reviews school-operations workflow correctness and user/persona fit. |
| Release Authority | Controls release posture through `docs/CURRENT_RELEASE_STATUS.md` and current-head evidence. |
| Independent Reviewer | Any qualified reviewer who did not author the work being approved. |

## Non-Negotiable Review Rules

1. The implementer cannot be the sole reviewer.
2. TC cannot self-approve TC-authored work.
3. Chat assertions are not evidence.
4. Historical PASS/GO/SHIP claims do not override current authority.
5. Screenshots alone do not prove module completion.
6. Frontend registry coverage does not prove backend/runtime completion.
7. Dashboard rendering does not prove module completion.
8. Sample/template data does not prove production readiness.
9. Every Certified promotion requires evidence and independent review.
10. Any material security, tenant, permission, data ownership, or dashboard certification change requires review before merge/promotion.

## Review Stages

### Stage 1: Planning Review

Purpose: confirm module boundaries, order, dependencies, and dashboard fit before implementation.

| Activity | Product Direction Owner | Implementer | Technical Reviewer | Security Reviewer | QA/Evidence Reviewer | Product Workflow Reviewer | Release Authority |
|---|---|---|---|---|---|---|---|
| Define module scope | A/R | C | C | C | I | C | I |
| Define data ownership | C | R | A | C | I | C | I |
| Define permission model | C | R | C | A | I | C | I |
| Define dashboard fit | C | R | A | C | C | C | I |
| Define evidence requirements | C | R | C | C | A | C | I |
| Approve plan for implementation | C | I | A | A for security-sensitive modules | A for evidence path | C | I |

### Stage 2: Implementation Review

Purpose: verify code, schema, API, frontend, and wiring before evidence promotion.

| Activity | Product Direction Owner | Implementer | Technical Reviewer | Security Reviewer | QA/Evidence Reviewer | Product Workflow Reviewer | Release Authority |
|---|---|---|---|---|---|---|---|
| Backend models/services/API | I | R | A | C | C | I | I |
| Frontend routes/workflows | I | R | A | C | C | C | I |
| Tenant enforcement | I | R | C | A | C | I | I |
| Action-level permissions | I | R | C | A | C | C | I |
| Audit events | I | R | C | A | C | C | I |
| Dashboard source service | I | R | A | C | C | C | I |
| Drilldowns/exports | I | R | C | A | C | C | I |

### Stage 3: Evidence Review

Purpose: verify proof before module/dashboard status promotion.

| Activity | Product Direction Owner | Implementer | Technical Reviewer | Security Reviewer | QA/Evidence Reviewer | Product Workflow Reviewer | Release Authority |
|---|---|---|---|---|---|---|---|
| Backend test proof | I | R | C | C | A | I | I |
| Frontend test proof | I | R | C | C | A | I | I |
| Tenant/permission tests | I | R | C | A | A | I | I |
| Runtime smoke proof | I | R | C | C | A | C | I |
| Screenshot/Playwright proof | I | R | I | C | A | C | I |
| Evidence packet completeness | I | R | C | C | A | C | I |
| Matrix row update | C | R | C | C | A | C | I |

### Stage 4: Certification Review

Purpose: decide whether a module or dashboard may be marked Certified.

| Activity | Product Direction Owner | Implementer | Technical Reviewer | Security Reviewer | QA/Evidence Reviewer | Product Workflow Reviewer | Release Authority |
|---|---|---|---|---|---|---|---|
| Certify module architecture | I | I | A | C | C | C | I |
| Certify security posture | I | I | C | A | C | I | I |
| Certify workflow correctness | C | I | C | C | C | A | I |
| Certify evidence completeness | I | I | C | C | A | C | I |
| Update module status to Certified | I | R | A | A if sensitive | A | C | I |
| Update dashboard status to Certified | I | R | A | A if sensitive | A | C | I |

### Stage 5: Release Authority Review

Purpose: determine whether release posture changes. This is separate from module certification.

| Activity | Product Direction Owner | Implementer | Technical Reviewer | Security Reviewer | QA/Evidence Reviewer | Product Workflow Reviewer | Release Authority |
|---|---|---|---|---|---|---|---|
| Current-head release packet | I | R | C | C | A | I | A |
| Release-status update | I | C | C | C | C | I | A |
| GO/NO-GO decision | I | I | C | C | C | I | A |

Module certification does not automatically create production GO.

## Module Certification Checklist

A module cannot be marked Certified unless all are complete:

- [ ] module row exists in `CROWN_MODULE_COMPLETION_MATRIX.md`
- [ ] data ownership row exists in `CROWN_MODULE_DATA_OWNERSHIP_MATRIX.md`
- [ ] permission row exists in `CROWN_MODULE_PERMISSION_MATRIX.md`
- [ ] dashboard fit row exists if dashboard-visible
- [ ] backend app/service/API verified
- [ ] models verified
- [ ] migrations verified where applicable
- [ ] tenant enforcement tested
- [ ] action-level permissions tested
- [ ] sensitive data redaction tested where applicable
- [ ] small-cell suppression tested where applicable
- [ ] audit events tested where applicable
- [ ] frontend route/workflow verified
- [ ] runtime proof current
- [ ] evidence packet linked
- [ ] independent technical review complete
- [ ] independent security review complete where applicable
- [ ] QA/evidence review complete
- [ ] product workflow review complete where applicable

## Dashboard Certification Checklist

A dashboard cannot be marked Certified unless all are complete:

- [ ] dashboard row exists in `CROWN_DASHBOARD_FIT_MATRIX.md`
- [ ] source module status supports dashboard promotion
- [ ] live service/API or certified snapshot source verified
- [ ] sample/template/fallback data absent from production-ready path
- [ ] provenance shown or inspectable
- [ ] freshness SLA defined and tested
- [ ] stale/unavailable behavior tested
- [ ] role access tested by dashboard key
- [ ] tenant access tested
- [ ] drilldown contract tested or explicitly marked aggregate-only
- [ ] export policy tested if export exists
- [ ] screenshot/Playwright proof current
- [ ] independent review complete

## Sensitive Module Review Requirement

The following modules always require Security Reviewer signoff before Certified status:

- billing-tuition-ledger
- financial-aid
- student-care-discipline
- health-office
- safety-security
- hr
- spiritual-life
- volunteer-management
- advancement-operations
- board-governance
- network-benchmarking
- data-migration
- integrations-automation
- dashboard-certification-center

## Rejection and Resubmission

If any reviewer rejects a module or dashboard promotion:

1. The row remains at its prior status.
2. The rejection reason is recorded in the matrix row or linked evidence packet.
3. The implementer corrects the issue.
4. The same evidence category is re-reviewed.
5. Certification cannot proceed until the rejection is closed.

## Revocation

Certified status must be revoked or downgraded if:

- source evidence becomes stale
- current-head tests fail
- tenant or permission regression is found
- sample/template data re-enters a production-ready dashboard
- dashboard source switches to fallback without approved exception
- data ownership changes without review
- sensitive data leak is discovered
- release authority supersedes prior certification

## Required Evidence Location

Evidence should be linked from the relevant matrix row. Preferred evidence locations:

```text
audit-artifacts/module-completion/<timestamp>/
audit-artifacts/dashboard-certification/<timestamp>/
audit-artifacts/runtime-proof/<timestamp>/
docs/release/evidence/<timestamp>/
```

Evidence generated locally is not authoritative until committed, attached, or otherwise linked in a reviewable form.

## Final Rule

No module, dashboard, or release posture may be promoted by the same person or agent that authored the work without independent review.
