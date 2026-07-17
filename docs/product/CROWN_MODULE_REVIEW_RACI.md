# CROWN Module Review RACI

**Status:** Planning control matrix  
**Parent canon:** `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`  
**Release authority:** `docs/CURRENT_RELEASE_STATUS.md`

## Purpose

This document defines review and approval responsibilities for CROWN module and dashboard work. It prevents self-approval, unclear ownership, premature certification, and unsupported release claims.

Development tools and automated review systems may assist with inspection, implementation, testing, analysis, and evidence preparation. They do not provide independent approval, security authorization, product acceptance, or release authority.

## Authority hierarchy

| Document | Controls |
|---|---|
| `docs/CURRENT_RELEASE_STATUS.md` | Repository release posture, GO/NO-GO, release freeze, and current-head evidence authority. |
| `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md` | Module and dashboard product architecture, order, vocabulary, and certification prerequisites. |
| `docs/product/CROWN_MODULE_COMPLETION_MATRIX.md` | Row-level module status and evidence requirements. |
| `docs/product/CROWN_MODULE_DATA_OWNERSHIP_MATRIX.md` | Canonical data ownership and duplicate-truth prevention. |
| `docs/product/CROWN_MODULE_PERMISSION_MATRIX.md` | Action-level permission and security requirements. |
| `docs/product/CROWN_DASHBOARD_FIT_MATRIX.md` | Dashboard-to-module fit and certification requirements. |
| `docs/product/CROWN_MODULE_REVIEW_RACI.md` | Review and approval routing. |

This file does not approve production release.

## RACI definitions

| Code | Meaning |
|---|---|
| R | Responsible: performs the work or prepares evidence. |
| A | Accountable: owns the decision for that stage. |
| C | Consulted: provides relevant subject-matter input. |
| I | Informed: receives status but does not approve. |

## Role definitions

| Role | Description |
|---|---|
| Product Direction Owner | Defines priorities, product intent, market fit, and module scope. |
| Implementer | Writes code, documentation, tests, or evidence. Cannot independently approve the work produced. |
| Engineering Support | Assists with inspection, implementation, evidence organization, and analysis. Cannot approve work it produced. |
| Technical Reviewer | Reviews architecture, maintainability, code structure, data ownership, API shape, and integration risk. |
| Security Reviewer | Reviews tenant isolation, permissions, sensitive data, redaction, exports, and auditability. |
| QA / Evidence Reviewer | Reviews tests, runtime proof, browser artifacts, and evidence completeness. |
| Product Workflow Reviewer | Reviews school-operations workflow correctness and user or persona fit. |
| Release Authority | Controls release posture through the canonical release record and current-head evidence. |
| Automated Review Support | Produces findings or suggestions that must be evaluated and dispositioned by accountable humans. It is not independent approval. |
| Independent Reviewer | A qualified person who did not author the work being approved and whose review is captured in a durable record. |

## Non-negotiable review rules

1. The implementer cannot be the sole reviewer.
2. The Product Direction Owner cannot independently approve their own authored work where independent review is required.
3. Engineering support cannot approve work it produced.
4. Automated findings are evidence inputs, not independent approval.
5. Chat assertions and unretained conversations are not evidence.
6. Historical PASS, GO, or SHIP claims do not override current authority.
7. Screenshots alone do not prove module completion.
8. Frontend registry coverage does not prove backend or runtime completion.
9. Dashboard rendering does not prove module completion.
10. Sample or template data does not prove production readiness.
11. Every Certified promotion requires current evidence and captured human review.
12. Material security, tenant, permission, data-ownership, or dashboard-certification changes require qualified review before promotion or release use.

## Accepted review evidence

Review evidence may be captured as:

- a GitHub pull-request review;
- a GitHub pull-request or issue comment from the accountable reviewer;
- a signed or attributable review memorandum;
- a committed review summary with identified reviewer and date;
- a security, QA, or architecture report with findings and dispositions;
- CI and automated-analysis output supporting, but not replacing, human review.

## Review stages

### Stage 1: Planning review

Confirm module boundaries, order, dependencies, data ownership, permissions, dashboard fit, and evidence requirements before implementation.

### Stage 2: Implementation review

Verify code, schema, API, frontend, tenant enforcement, permissions, audit behavior, and wiring before evidence promotion.

### Stage 3: Evidence review

Verify backend and frontend tests, tenant and permission tests, runtime proof, browser evidence, and evidence-packet completeness.

### Stage 4: Certification review

A qualified human reviewer determines whether the evidence supports module or dashboard certification. Certification does not create production GO.

### Stage 5: Release-authority review

The designated release authority evaluates the current-head release packet and controls any change to release posture.

## Module certification checklist

A module cannot be marked Certified unless all applicable items are complete:

- [ ] module row exists in `CROWN_MODULE_COMPLETION_MATRIX.md`;
- [ ] data-ownership row exists in `CROWN_MODULE_DATA_OWNERSHIP_MATRIX.md`;
- [ ] permission row exists in `CROWN_MODULE_PERMISSION_MATRIX.md`;
- [ ] dashboard-fit row exists when dashboard-visible;
- [ ] backend app, service, and API verified;
- [ ] models and migrations verified where applicable;
- [ ] tenant enforcement tested;
- [ ] action-level permissions tested;
- [ ] sensitive-data controls tested where applicable;
- [ ] audit events tested where applicable;
- [ ] frontend route and workflow verified;
- [ ] runtime proof is current;
- [ ] evidence packet is linked;
- [ ] qualified human review evidence is captured;
- [ ] blocking corrections are closed.

## Dashboard certification checklist

A dashboard cannot be marked Certified unless all applicable items are complete:

- [ ] dashboard row exists in `CROWN_DASHBOARD_FIT_MATRIX.md`;
- [ ] source-module status supports promotion;
- [ ] live service, API, or certified snapshot source is verified;
- [ ] sample, template, or fallback data is absent from the production-ready path;
- [ ] provenance and freshness behavior are defined and tested;
- [ ] role and tenant access are tested;
- [ ] drilldown and export policies are tested where applicable;
- [ ] browser or runtime proof is current;
- [ ] qualified human review evidence is captured;
- [ ] blocking corrections are closed.

## Sensitive module review requirement

Billing, accounting, financial aid, student care, health, safety, human resources, governance, data migration, integrations, and other sensitive modules require qualified security review before Certified status.

## Rejection, resubmission, and revocation

When review identifies a blocker, the item remains at its prior status until the finding is corrected and re-reviewed. Certified status must be revoked or downgraded when current evidence no longer supports it.
