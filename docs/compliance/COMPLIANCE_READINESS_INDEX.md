# CROWN Compliance Readiness Index

**Status:** Active final-sprint evidence index  
**Date:** 2026-07-19  
**Release posture:** CONTROLLED SANDBOX CANDIDATE / PRODUCTION NOT APPROVED

## Decision rules

- A written policy is **DOCUMENTED**, not certified.
- A source control is **IMPLEMENTED**, not operationally proven.
- A passing repository test does not replace deployed-runtime, contractual, legal, or exercise evidence.
- No broad "FERPA certified," "COPPA certified," or universal compliance claim is authorized.
- Payment processing is deferred until the Founder/Product Owner selects a provider and gives written implementation authorization.
- Buyer, successor, and ownership-transfer work is proposal-only until the Founder/Product Owner opens that lane.

## Readiness register

| Deliverable | Pilot requirement | Production/GA requirement | Current status | Next evidence |
|---|---:|---:|---|---|
| Student-data privacy and compliance position | Yes | Yes | DOCUMENTED / NOT LEGAL CERTIFICATION | Legal and customer review; operational evidence |
| FERPA service-provider position | Yes | Yes | DOCUMENTED | DPA terms, school-official criteria, role/tenant runtime proof, support-access audit |
| COPPA applicability and consent position | Yes | Yes | DOCUMENTED | Under-13 feature/account inventory, notice/consent path, retention/deletion verification |
| PPRA feature assessment | As applicable | As applicable | OPEN | Survey/protected-topic inventory, notice, consent/opt-out and audit evidence |
| CIPA claim boundary | Yes | Yes | DOCUMENTED | Confirm no filtering/certification claim; identify any administrative support only |
| State student-data privacy applicability matrix | Target-market dependent | Yes | OPEN | State-by-state legal review for intended customer jurisdictions |
| Data Processing Addendum template | Yes | Yes | DRAFT / NOT LEGAL-SIGNED | Counsel review, customer responsibility schedule, executed customer terms |
| Privacy policy and customer notices | Yes | Yes | OPEN / PARTIAL | Approved public policy, school/parent/student notices, version control |
| Data inventory and classification | Yes | Yes | PARTIAL | Model/domain inventory including sensitive, health, discipline, pastoral, financial and document data |
| Data-flow and subprocessor register | Yes | Yes | OPEN / PARTIAL | Actual production vendors, data categories, locations, DPA and security status |
| Data retention and deletion policy | Yes | Yes | DOCUMENTED / EVIDENCE REQUIRED | Domain retention schedule, deletion/anonymization rehearsal, backup expiration evidence |
| Parent/student access, correction and export procedures | Yes | Yes | PARTIAL | End-to-end authorized request tests and customer operating procedure |
| Support-access policy | Yes | Yes | DOCUMENTED / EVIDENCE REQUIRED | Time-bounded privileged-access exercise, audit records and post-event review |
| Incident-response policy | Yes | Yes | DOCUMENTED / EVIDENCE REQUIRED | Tabletop or controlled exercise, notification matrix and retained report |
| Tenant isolation and cross-school denial | Yes | Yes | SOURCE CONTROLS SUBSTANTIAL | Same-SHA authenticated runtime, audit completeness and remaining convergence proof |
| Role and permission enforcement | Yes | Yes | SOURCE/MODULE EVIDENCE SUBSTANTIAL | Deployed administrator, teacher, parent and elevated-role proof |
| Audit logging and retention | Yes | Yes | PARTIAL | Complete structured tenant/override/support events and retention proof |
| External secrets management | Yes | Yes | ARCHITECTURE DOCUMENTED | External identity, least privilege, secret retrieval, audit, rotation and revocation evidence |
| Break-glass access | Yes | Yes | DOCUMENTED / NOT EXERCISED | Controlled exercise, approval, audit, revocation and post-event review |
| Backup, rollback and restore | Yes | Yes | ARCHITECTURE IMPLEMENTED / DRILL OPEN | Application rollback, isolated restore, reconciliation and measured RTO/RPO |
| Accessibility verification | Yes | Yes | PARTIAL | Final route sweep, issue register and accepted exceptions |
| Sandbox/no-real-data policy | Yes | Yes | DOCUMENTED | Enforcement and sample-data provenance verification |
| Payment processor | No for non-payment scope | Required only before payment activation | DEFERRED / NO PROVIDER SELECTED | Founder/Product Owner selection, signed agreement and new bounded implementation authorization |
| Buyer/successor handoff | No | Not a current release gate unless separately authorized | PROPOSAL ONLY / DEFERRED | Founder/Product Owner opens lane after transaction or handoff direction is established |
| Final compliance review and approval | Yes | Yes | NOT COMPLETE | Evidence packet, legal disposition and Founder/Product Owner decision |

## Current compliance priority queue

### P0 — release and pilot evidence

1. Run the exact-SHA authenticated runtime campaign for role, tenant, network, console, screenshot and data-provenance evidence.
2. Complete structured tenant, override, privileged-access and disclosure audit evidence.
3. Execute application rollback and isolated database restore drills with measured RTO/RPO.
4. Execute external secret-store identity, rotation, failed-rotation, audit and break-glass exercises.
5. Complete the data inventory, classification, retention and subprocessor register.
6. Conduct an incident-response tabletop or controlled exercise.

### P1 — legal and customer readiness

1. Obtain legal review of FERPA, COPPA, PPRA, state-law and contract positions.
2. Finalize the DPA, privacy policy, customer responsibility schedule and required notices.
3. Build the intended-market state student-data privacy matrix.
4. Establish parent/student access, correction, export, deletion and complaint procedures.
5. Reconcile accessibility findings and customer procurement requirements.

### Explicitly deferred

- Payment-provider selection and implementation.
- Buyer identification, transaction support and ownership-transfer execution.
- Successor clean-room or handoff execution until specifically authorized.
- Any external claim of legal certification before evidence and review are complete.

## Current approved statement

> CROWN has a documented student-data privacy and compliance framework with substantial repository-level security, tenant, role, audit and governance controls. Final deployed-runtime, operational, contractual, state-law and legal validation remains in progress.
