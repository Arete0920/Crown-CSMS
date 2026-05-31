# CROWN Final 95+ Compliance and Customer Readiness Audit - 2026-05-30

Status: CONNECTOR-SAFE CONTROL ARTIFACT
Authority: Non-shipping audit document until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Purpose

A production-ready school management system is not complete if the code works but the customer trust, privacy, compliance, support, deployment, and operational readiness controls are incomplete.

This document defines the required compliance/customer-readiness closure stack for the final 95+ sprint.

## Current posture

Status: NOT DONE

Reason: Connector inspection can define the required artifact stack, but final compliance/customer readiness requires actual reviewed documents, assigned owners, and evidence. Do not score this area 95+ until every row below is complete and committed.

## Required compliance/customer readiness artifacts

| Artifact | Purpose | Status | Required final evidence |
|---|---|---|---|
| FERPA posture statement | Explain how CROWN handles education records and school-controlled data | NOT DONE | Reviewed FERPA statement and operating controls |
| COPPA posture statement | Explain child data handling, consent assumptions, and school-as-agent posture | NOT DONE | Reviewed COPPA statement and controls |
| Data Processing Addendum template | Customer contract data-processing obligations | NOT DONE | DPA draft approved for customer review |
| Privacy/security summary | Customer-facing trust summary | NOT DONE | Published or release-ready privacy/security summary |
| Data retention policy | Define retention, purge, archival, legal hold | NOT DONE | Policy plus purge/control evidence |
| Support access policy | Define staff/support access to school data | NOT DONE | Policy plus audit trail expectations |
| Incident response plan | Define incident intake, triage, notification, escalation | NOT DONE | IR plan and owner workflow |
| Backup/restore proof | Define and prove backup/restore process | NOT DONE | Backup/restore test evidence |
| Subprocessor register | Identify cloud/services/providers used | NOT DONE | Register reviewed and current |
| Sandbox data policy | Confirm sandbox/demo data restrictions and no real student data expectations | NOT DONE | Sandbox policy and data reset controls |
| Customer onboarding checklist | Define implementation, configuration, imports, validation | NOT DONE | Customer onboarding runbook |
| Production support runbook | Define monitoring, escalation, rollback, support channels | NOT DONE | Operational runbook |
| Accessibility readiness | Confirm WCAG/accessibility proof for release surfaces | NOT DONE | A11y test output and exceptions register |
| Security configuration checklist | Confirm env secrets, CORS/CSRF, HTTPS, HSTS, tenant enforcement | NOT DONE | Production config checklist and deploy proof |
| Microsoft 365 readiness checklist | Confirm Entra, Graph, Teams/MS365 education configuration expectations | NOT DONE | M365 readiness checklist and admin screenshot/evidence references |

## Required customer-facing release pack

Before any buyer/customer-facing production-release claim, create:

1. `docs/release/final-95-plus-sprint/FINAL_CUSTOMER_TRUST_PACKET.md`
2. `docs/release/final-95-plus-sprint/FINAL_PRODUCTION_SUPPORT_RUNBOOK.md`
3. `docs/release/final-95-plus-sprint/FINAL_IMPLEMENTATION_ONBOARDING_RUNBOOK.md`
4. `docs/release/final-95-plus-sprint/FINAL_PRIVACY_SECURITY_COMPLIANCE_SUMMARY.md`
5. `docs/release/final-95-plus-sprint/FINAL_BACKUP_RESTORE_PROOF.md`
6. `docs/release/final-95-plus-sprint/FINAL_SANDBOX_DATA_POLICY.md`

## Minimum production-readiness controls

### Privacy and records

- School tenant data must remain isolated by tenant.
- Parent/student access must be scoped to permitted household/student records.
- Staff access must be role- and object-scoped.
- Export/reporting routes must be authorized and auditable.
- Retention/purge behavior must be documented and tested.

### Security and operations

- Production secrets must be environment-supplied.
- Debug must be off in production.
- CORS must be explicit.
- CSRF trusted origins must be explicit.
- HTTPS/HSTS must be configured for production context.
- Audit logging must cover sensitive reads/writes.
- Idempotency must protect mutating financial/admissions flows.

### Customer readiness

- School onboarding flow must be documented.
- Data migration/import flow must be documented.
- Support escalation path must be documented.
- Known limitations must be actively controlled and not hidden.
- Sandbox/demo behavior must be clearly separated from production behavior.

### Microsoft 365 readiness

- Entra/AAD login assumptions must be documented.
- M365/Graph sender requirements must be documented.
- Teams/classroom integration readiness must be documented and proven before sale as complete.
- Admin setup evidence must be captured before claiming M365 production readiness.

## Scoring rule

Compliance/customer readiness cannot score above 70 until artifacts exist.
It cannot score above 85 until artifacts are reviewed and internally consistent.
It cannot score 95+ until artifacts are evidence-backed, current, and aligned with production configuration proof.

## Current score

| Area | Score | Basis |
|---|---:|---|
| Compliance/customer readiness | 45 | Required artifact stack defined; proof not yet produced |

## Release impact

This is a production-release blocker for any unrestricted buyer/customer launch. It is not optional. Code completion alone is insufficient for 95+ production readiness.
