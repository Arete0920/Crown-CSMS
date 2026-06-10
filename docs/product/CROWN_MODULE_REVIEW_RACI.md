# CROWN Module Review RACI

Status: Planning Control Matrix
Parent Canon: `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`
Release Authority: `docs/CURRENT_RELEASE_STATUS.md`

## Purpose

This document defines review and approval responsibilities for CROWN module and dashboard completion. It exists to prevent self-approval, unclear ownership, premature certification, and unsupported release claims.

TC may set direction, priorities, and product intent, but TC cannot independently review or approve TC's own work. ChatGPT may draft, inspect, and organize evidence, but ChatGPT cannot approve work it authored. GitHub Copilot may serve as the independent review support path when its review output is captured in VS Code/GitHub or committed evidence.

## Authority Hierarchy

| Document | Controls |
|---|---|
| `docs/CURRENT_RELEASE_STATUS.md` | Repository release posture, GO/NO-GO, release freeze, current-head evidence authority. |
| `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md` | Module/dashboard product architecture, order, vocabulary, certification prerequisites. |
| `docs/product/CROWN_MODULE_COMPLETION_MATRIX.md` | Row-level module status and evidence requirements. |
| `docs/product/CROWN_MODULE_DATA_OWNERSHIP_MATRIX.md` | Canonical data ownership and duplicate-truth prevention. |
| `docs/product/CROWN_MODULE_PERMISSION_MATRIX.md` | Action-level permission and security requirements. |
| `docs/product/CROWN_DASHBOARD_FIT_MATRIX.md` | Dashboard-to-module fit and certification requirements. |
| `docs/product/CROWN_MODULE_REVIEW_RACI.md` | Review and approval routing, including Copilot review evidence requirements. |

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
| ChatGPT Support | Drafts, inspects, organizes evidence, and prepares repo artifacts. Cannot approve work it authored. |
| Copilot Reviewer | Reviews through VS Code/GitHub. Review is valid only when the output is captured as evidence. |
| Technical Reviewer | Reviews architecture, code structure, data ownership, API shape, and integration risk. May be served by captured Copilot review if adequate. |
| Security Reviewer | Reviews tenant isolation, permissions, sensitive data, redaction, exports, and auditability. May be served by captured Copilot review if adequate. |
| QA / Evidence Reviewer | Reviews tests, runtime proof, screenshots, Playwright artifacts, and evidence completeness. May be served by captured Copilot review if adequate. |
| Product Workflow Reviewer | Reviews school-operations workflow correctness and user/persona fit. TC provides product direction; approval still requires captured review evidence. |
| Release Authority | Controls release posture through `docs/CURRENT_RELEASE_STATUS.md` and current-head evidence. |
| Independent Reviewer | A qualified reviewer/tool path that did not author the work being approved, with review output captured as evidence. |

## Non-Negotiable Review Rules

1. The implementer cannot be the sole reviewer.
2. TC cannot self-approve TC-authored work.
3. ChatGPT cannot approve ChatGPT-authored work.
4. Copilot review is not valid unless its output is captured as evidence.
5. Chat assertions are not evidence.
6. Historical PASS/GO/SHIP claims do not override current authority.
7. Screenshots alone do not prove module completion.
8. Frontend registry coverage does not prove backend/runtime completion.
9. Dashboard rendering does not prove module completion.
10. Sample/template data does not prove production readiness.
11. Every Certified promotion requires evidence and review evidence.
12. Any material security, tenant, permission, data ownership, or dashboard certification change requires review before merge/promotion.

## Accepted Copilot Review Evidence

Copilot review evidence must be captured in at least one of these forms:

- GitHub PR review
- GitHub PR comment
- GitHub issue comment
- committed VS Code/Copilot review transcript or summary
- pasted Copilot review output committed into an evidence packet
- CI/check artifact that includes Copilot-generated review output and disposition

Do not mark a module, dashboard, or planning package as Copilot-reviewed unless one of those evidence forms exists.

## Review Stages

### Stage 1: Planning Review

Purpose: confirm module boundaries, order, dependencies, and dashboard fit before implementation.

| Activity | Product Direction Owner | Implementer | ChatGPT Support | Copilot Reviewer | Release Authority |
|---|---|---|---|---|---|
| Define module scope | A/R | C | R | C | I |
| Define data ownership | C | R | R | A when captured | I |
| Define permission model | C | R | R | A when captured | I |
| Define dashboard fit | C | R | R | A when captured | I |
| Define evidence requirements | C | R | R | A when captured | I |
| Approve plan for planning use | C | I | R | A when captured | I |

### Stage 2: Implementation Review

Purpose: verify code, schema, API, frontend, and wiring before evidence promotion.

| Activity | Product Direction Owner | Implementer | ChatGPT Support | Copilot Reviewer | Release Authority |
|---|---|---|---|---|---|
| Backend models/services/API | I | R | C | A when captured | I |
| Frontend routes/workflows | I | R | C | A when captured | I |
| Tenant enforcement | I | R | C | A when captured | I |
| Action-level permissions | I | R | C | A when captured | I |
| Audit events | I | R | C | A when captured | I |
| Dashboard source service | I | R | C | A when captured | I |
| Drilldowns/exports | I | R | C | A when captured | I |

### Stage 3: Evidence Review

Purpose: verify proof before module/dashboard status promotion.

| Activity | Product Direction Owner | Implementer | ChatGPT Support | Copilot Reviewer | Release Authority |
|---|---|---|---|---|---|
| Backend test proof | I | R | C | A when captured | I |
| Frontend test proof | I | R | C | A when captured | I |
| Tenant/permission tests | I | R | C | A when captured | I |
| Runtime smoke proof | I | R | C | A when captured | I |
| Screenshot/Playwright proof | I | R | C | A when captured | I |
| Evidence packet completeness | I | R | R | A when captured | I |
| Matrix row update | C | R | R | A when captured | I |

### Stage 4: Certification Review

Purpose: decide whether a module or dashboard may be marked Certified.

| Activity | Product Direction Owner | Implementer | ChatGPT Support | Copilot Reviewer | Release Authority |
|---|---|---|---|---|---|
| Certify module architecture | I | I | C | A when captured | I |
| Certify security posture | I | I | C | A when captured | I |
| Certify workflow correctness | C | I | C | A when captured | I |
| Certify evidence completeness | I | I | R | A when captured | I |
| Update module status to Certified | I | R | R | A when captured | I |
| Update dashboard status to Certified | I | R | R | A when captured | I |

### Stage 5: Release Authority Review

Purpose: determine whether release posture changes. This is separate from module certification.

| Activity | Product Direction Owner | Implementer | ChatGPT Support | Copilot Reviewer | Release Authority |
|---|---|---|---|---|---|
| Current-head release packet | I | R | R | C | A |
| Release-status update | I | C | C | C | A |
| GO/NO-GO decision | I | I | I | C | A |

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
- [ ] Copilot review evidence captured, or another qualified independent review evidence path captured
- [ ] corrections closed

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
- [ ] Copilot review evidence captured, or another qualified independent review evidence path captured
- [ ] corrections closed

## Sensitive Module Review Requirement

The following modules always require Security Reviewer/Copilot security-focused review evidence before Certified status:

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

If Copilot or another reviewer rejects a module or dashboard promotion:

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

No module, dashboard, or release posture may be promoted by the same person or agent that authored the work without captured review evidence. Copilot review is acceptable for this lane only when its output is captured as evidence.
