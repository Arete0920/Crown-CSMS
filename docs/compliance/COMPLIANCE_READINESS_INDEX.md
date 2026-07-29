# CROWN Compliance Readiness Index

**Status:** Active Lane 5 evidence index  
**Date:** 2026-07-29  
**Controlling issues:** #1629 and #1619  
**Supporting evidence status:** `docs/compliance/PRIVACY_COMPLIANCE_EVIDENCE_STATUS.md`  
**Release posture:** CONTROLLED SANDBOX CANDIDATE / PRODUCTION NOT APPROVED

## Decision rules

- A written policy is **DOCUMENTED**, not certified.
- A source control is **IMPLEMENTED**, not operationally proven.
- A passing repository test does not replace deployed-runtime, contractual, legal, or exercise evidence.
- No broad "FERPA certified," "COPPA certified," or universal compliance claim is authorized.
- Payment processing is deferred until the Founder/Product Owner selects a provider and gives written implementation authorization.
- Buyer, successor, and ownership-transfer work remains outside Lane 5 and requires separate transaction authority.
- Closed issue #1425 is superseded historical context; current Lane 5 authority is #1629.

## Readiness register

| Deliverable | Pilot requirement | Production/GA requirement | Current status | Next evidence |
|---|---:|---:|---|---|
| Student-data privacy and compliance position | Yes | Yes | DOCUMENTED / NOT LEGAL CERTIFICATION | Legal and customer review; operational evidence |
| FERPA service-provider position | Yes | Yes | DOCUMENTED | DPA terms, school-official criteria, role/tenant runtime proof, support-access audit |
| COPPA applicability and consent position | Yes | Yes | DOCUMENTED | Under-13 feature/account inventory, notice/consent path, retention/deletion verification |
| PPRA feature assessment | As applicable | As applicable | OPEN | Survey/protected-topic inventory, notice, consent/opt-out and audit evidence |
| CIPA claim boundary | Yes | Yes | DOCUMENTED | Confirm no filtering/certification claim; identify any administrative support only |
| State student-data privacy applicability matrix | Target-market dependent | Yes | OPEN | State-by-state legal review for intended customer jurisdictions |
| Data Processing Addendum template | Yes | Yes | DRAFT / NOT LEGAL-SIGNED | Counsel review, provider legal entity, customer responsibility schedule, executed customer terms |
| Privacy policy and customer notices | Yes | Yes | OPEN / PARTIAL | Approved public policy, school/parent/student notices, version control |
| Data inventory and classification | Yes | Yes | PARTIAL | Model/domain/storage-path inventory including sensitive, health-adjacent, discipline, pastoral, financial, authentication, document and audit data |
| Data-flow and subprocessor register | Yes | Yes | OPEN / SCAFFOLD | Actual production vendors, data categories, locations, DPA/security status, notice and retention obligations |
| Data retention and deletion policy | Yes | Yes | DOCUMENTED / EVIDENCE REQUIRED | Domain retention schedule, deletion/anonymization rehearsal, backup expiration and legal-hold evidence |
| Parent/student access, correction and export procedures | Yes | Yes | PARTIAL | End-to-end authorized request tests and customer operating procedure |
| Support-access policy | Yes | Yes | DOCUMENTED / EVIDENCE REQUIRED | Time-bounded privileged-access exercise, audit records, revocation and post-event review |
| Incident-response policy | Yes | Yes | DOCUMENTED / EVIDENCE REQUIRED | Tabletop or controlled exercise, notification matrix and retained report |
| Tenant isolation and cross-school denial | Yes | Yes | SOURCE CONTROLS SUBSTANTIAL / RUNTIME OPEN | Same-SHA authenticated runtime, object-level authorization, audit completeness and remaining convergence proof |
| Role and permission enforcement | Yes | Yes | SOURCE/MODULE EVIDENCE SUBSTANTIAL | Deployed administrator, teacher, parent, support and elevated-role proof |
| Audit logging and retention | Yes | Yes | SOURCE PARTIAL / RETENTION OPEN | Complete structured tenant/override/support/disclosure events and retention proof |
| External secrets management | Yes | Yes | ARCHITECTURE DOCUMENTED | External identity, least privilege, secret retrieval, audit, rotation and revocation evidence |
| Break-glass access | Yes | Yes | DOCUMENTED / NOT EXERCISED | Controlled exercise, approval, audit, revocation and post-event review |
| Backup, rollback and restore | Yes | Yes | ARCHITECTURE IMPLEMENTED / DRILL OPEN | Application rollback, isolated restore, reconciliation, backup expiration and measured RTO/RPO |
| Accessibility verification | Yes | Yes | PARTIAL | Final route sweep, issue register and accepted exceptions |
| Sandbox/no-real-data policy | Yes | Yes | DOCUMENTED | Enforcement and sample-data provenance verification |
| Payment processor | No for non-payment scope | Required only before payment activation | DEFERRED / NO PROVIDER SELECTED | Founder/Product Owner selection, signed agreement and new bounded implementation authorization |
| Final compliance review and approval | Yes | Yes | NOT COMPLETE | Evidence packet, qualified legal disposition and Founder/Product Owner decision |

## Current compliance priority queue

### P0 — repository and operational evidence

1. Complete the data inventory, classification, processing map, storage paths and subprocessor register.
2. Establish the domain retention schedule, correction/export/deletion procedures, backup expiration and legal-hold handling.
3. Complete exact-SHA authenticated runtime evidence for role, tenant, object authorization, support access, audit, network and provenance.
4. Execute application rollback and isolated database restore drills with reconciliation and measured RTO/RPO.
5. Execute external secret-store identity, rotation, failed-rotation, audit, revocation and break-glass exercises.
6. Conduct an incident-response tabletop or controlled exercise and retain the report.

### P1 — legal and customer readiness

1. Obtain qualified legal review of FERPA, COPPA, PPRA, CIPA claim boundaries, state-law obligations and contract positions.
2. Finalize the DPA, privacy policy, customer responsibility schedule, notices and subprocessor terms.
3. Build the intended-market state student-data privacy matrix.
4. Establish school, parent and student access, correction, export, deletion and complaint procedures.
5. Reconcile accessibility findings and customer procurement requirements.

### Explicitly deferred or separately controlled

- Payment-provider selection and implementation.
- Buyer identification, transaction support and ownership-transfer execution.
- Successor clean-room or handoff execution until specifically authorized.
- Any external claim of legal certification before evidence and review are complete.

## Current approved statement

> CROWN has a documented student-data privacy and compliance framework with substantial repository-level controls. Final deployed-runtime, operational, contractual, jurisdiction-specific, and legal validation remains in progress.
