# CROWN Module Review RACI

**Status:** ACTIVE CONTROL MATRIX  
**Effective baseline:** 2026-08-07  
**Parent canon:** `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`  
**Release authority:** `docs/CURRENT_RELEASE_STATUS.md` and GitHub issue `#1619`

## Purpose

This file is the required independent-review control for full-module completion. It does not authorize a merge, deployment, production promotion, or release. It does not replace the bounded production-release authority in issue `#1619`.

## Authority rules

- Founder/Product Owner: accountable for product direction, priority, scope acceptance, and business decisions.
- Work Author: responsible for implementation, tests, remediation, and evidence assembly.
- Independent Reviewer: responsible for independent inspection of the exact evidence packet and retained review findings/signoff. The reviewer must be a human who did not author the reviewed work.
- Security/Privacy Reviewer: required when a module handles Highly Sensitive data, cross-tenant administration, identity, security incidents, health, discipline, donor/payment/financial information, or network aggregation.
- Release Authority: governed by current repository controls and issue `#1619`; module review does not itself authorize production deployment.
- The Founder/Product Owner cannot independently review or approve work they authored.
- Automated systems and tools may assist with implementation and evidence but are not independent reviewers or approval authorities.
- `SOLO_DEVELOPER_APPROVED_WORKAROUND` may be used only for bounded governance when its conditions are satisfied. It is not independent human review and cannot be recorded as one.

## RACI legend

- `A` — Accountable for product/scope decision.
- `R` — Responsible for doing the work.
- `I` — Independently reviews exact-head evidence and findings.
- `S` — Security/privacy specialist review required.
- `RA` — Release authority under repository/production controls.
- `UNASSIGNED` — no qualified independent reviewer is currently recorded for the full-module certification row.

## Current role assignment

| Responsibility | Current assignment |
|---|---|
| Product/scope accountability | Founder/Product Owner |
| Work author | PR/commit author for the bounded module change |
| Independent module reviewer | **UNASSIGNED unless explicitly retained on the module evidence record** |
| Security/privacy specialist reviewer | **UNASSIGNED unless explicitly retained where required** |
| Release authority | Current repository governance + issue `#1619`; never inferred from module review |

## Module review lanes

Every module below currently has `UNASSIGNED` independent full-module review unless a later evidence record names a qualified reviewer. This is deliberate: no reviewer is inferred from historical involvement, repository access, tooling, or automated checks.

| Phase | Module Key | Independent Reviewer | Security/Privacy Review | Certification authority |
|---|---|---|---|---|
| 0 | `tenant-school-context` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 0 | `identity-users-roles` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 0 | `rbac-permissions` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 0 | `audit-logging` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 0 | `entitlements-subscriptions` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 0 | `retention-rollover` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 0 | `dashboard-certification-contract` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 1 | `school-year-grade` | UNASSIGNED | AS REQUIRED | Exact evidence + independent signoff |
| 1 | `staff-user-role` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 1 | `family-guardian-household` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 1 | `student-master` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 1 | `enrollment-registrar` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 1 | `courses-sections-rosters` | UNASSIGNED | AS REQUIRED | Exact evidence + independent signoff |
| 1 | `attendance` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 1 | `gradebook` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 1 | `transcripts-reportcards` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 1 | `student-care-discipline` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 2 | `admissions` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 2 | `re-enrollment` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 2 | `billing-tuition-ledger` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 2 | `financial-aid` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 2 | `communications` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 2 | `parent-family-portal` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 2 | `teacher-portal` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 2 | `administrator-portal` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 3 | `scheduling` | UNASSIGNED | AS REQUIRED | Exact evidence + independent signoff |
| 3 | `activities-athletics` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 3 | `health-office` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 3 | `transportation` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 3 | `food-service` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 3 | `facilities` | UNASSIGNED | AS REQUIRED | Exact evidence + independent signoff |
| 3 | `safety-security` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 3 | `hr` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 3 | `it-support` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 4 | `fine-arts` | UNASSIGNED | AS REQUIRED | Exact evidence + independent signoff |
| 4 | `library-media` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 4 | `extended-care` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 4 | `summer-camp` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 4 | `spiritual-life` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 4 | `service-outreach-portrait` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 4 | `volunteer-management` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 4 | `advancement-operations` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 4 | `alumni-relations` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 4 | `board-governance` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 4 | `curriculum-pd` | UNASSIGNED | AS REQUIRED | Exact evidence + independent signoff |
| 4 | `network-benchmarking` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 5 | `implementation-success` | UNASSIGNED | AS REQUIRED | Exact evidence + independent signoff |
| 5 | `data-migration` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 5 | `integrations-automation` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 5 | `compliance-audit` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 5 | `revenue-operations` | UNASSIGNED | REQUIRED | Exact evidence + independent signoff |
| 5 | `release-reliability` | UNASSIGNED | AS REQUIRED | Exact evidence + independent signoff |
| 5 | `dashboard-certification-center` | UNASSIGNED | AS REQUIRED | Exact evidence + independent signoff |

## Independent review packet

A reviewer signoff must identify:

1. module key and exact source SHA;
2. bounded scope reviewed;
3. data-ownership row inspected;
4. permission and tenant evidence inspected;
5. API/service/error/audit evidence inspected;
6. frontend and direct-route evidence inspected;
7. dashboard provenance/freshness/performance evidence inspected when applicable;
8. security/privacy findings and disposition when required;
9. exact tests/runtime artifacts inspected;
10. unresolved risks or explicit statement that required findings are resolved;
11. reviewer name, role, date, and statement that the reviewer did not author the reviewed work.

## Promotion rule

No module or dashboard may be marked `Certified` while its independent-review field is `UNASSIGNED`, while required security/privacy review is unresolved, or while any required evidence is pending, failed, stale, or not tied to the reviewed source SHA.
