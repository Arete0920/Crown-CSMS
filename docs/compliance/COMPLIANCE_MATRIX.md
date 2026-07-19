# CROWN Compliance Control Matrix

**Status:** Current control and evidence matrix  
**Date:** 2026-07-19  
**Release posture:** CONTROLLED SANDBOX CANDIDATE / PRODUCTION NOT APPROVED

## Status definitions

- **IMPLEMENTED:** source or repository control exists, but may still require runtime or operational evidence.
- **DOCUMENTED:** policy or procedure exists, but implementation or execution proof is incomplete.
- **EVIDENCE REQUIRED:** the control cannot be promoted without current proof.
- **DEFERRED:** outside current authorized implementation scope.
- **NOT APPLICABLE AS CERTIFICATION:** CROWN may support customer obligations but does not issue or replace the customer's legal certification.

## Federal and cross-cutting matrix

| Domain | CROWN responsibility | School/customer responsibility | Current repository position | Remaining evidence |
|---|---|---|---|---|
| FERPA | Process school-controlled education records only for authorized institutional purposes; enforce tenant, role, access, audit, retention, disclosure, and contract controls | Determine legal basis, annual notice, legitimate educational interest, records-rights procedures, and customer-specific policies | DOCUMENTED; material tenant/RBAC controls IMPLEMENTED | Legal review, DPA approval, runtime tenant/role proof, support-access proof, retention/deletion proof, audit completeness |
| COPPA | Determine operator applicability; provide notice; limit under-13 collection to authorized school purposes; prevent unrelated commercial use; support review/deletion and reasonable security | Approve services and school-consent path where legally available; provide parent notice or obtain parental consent where required | DOCUMENTED | Applicability decision, direct-under-13 account inventory, notice/consent verification, retention/deletion test |
| PPRA | Support configurable notice, consent/opt-out, inspection, protected-topic handling, and audit where relevant | Adopt required policies, notify parents, administer consent/opt-out, and determine feature applicability | DOCUMENTED / FEATURE REVIEW REQUIRED | Survey and protected-topic inventory, notice/consent workflow evidence, customer configuration guidance |
| CIPA / E-Rate | Do not claim filtering certification; support administrative evidence only where implemented | Maintain internet safety policy, technology protection measures, public notice/hearing, and E-Rate certification | NOT APPLICABLE AS CROWN CERTIFICATION | Confirm no unsupported filtering/CIPA claims; document any administrative support scope |
| State student-data privacy | Support contractual restrictions, deletion, access, security, subprocessor, and no-sale/no-advertising commitments | Identify governing state law and school-specific obligations | EVIDENCE REQUIRED | State applicability matrix for intended markets and contract addenda |
| Breach notification | Detect, contain, investigate, preserve evidence, identify affected tenants/data, and notify under approved timelines | Provide contacts, cooperate, make customer/regulatory decisions where assigned | DOCUMENTED | Incident tabletop, notification matrix, contact validation, retained exercise evidence |
| Accessibility | Provide accessible product surfaces and test against defined standards | Define procurement and local accommodation requirements | PARTIAL IMPLEMENTATION / EVIDENCE REQUIRED | Final accessibility sweep, exception register, remediation and acceptance decisions |
| Records retention | Implement configurable retention, export, deletion/anonymization, backup expiration, and legal-hold-aware procedures | Define schedules and authorize deletion/export under law and policy | DOCUMENTED | Domain-level data inventory, retention schedule, deletion rehearsal, backup expiration proof |
| Subprocessors | Maintain register, purpose, data categories, location, security, contract/DPA status, and change process | Review and approve contract terms where required | DOCUMENTED / REGISTER INCOMPLETE | Current production subprocessor register and executed terms |
| Support access | Enforce least privilege, time limits, approval, audit, export restrictions, and break-glass review | Approve ordinary support access and receive incident reporting | DOCUMENTED / SOURCE CONTROLS PARTIAL | Runtime privileged-access evidence, break-glass exercise, post-event review |
| Security and secrets | Use identity-based access, external secret store, audit, rotation, and fail-closed configuration | Maintain authorized contacts and approve customer-managed integrations | IMPLEMENTED IN REPOSITORY / OPERATIONAL EVIDENCE REQUIRED | External identity, Key Vault/Vault audit, rotation, failed-rotation, revocation, break-glass exercise |
| Backup and recovery | Maintain encrypted backups, immutable rollback, tenant-aware restore procedures, and measured RTO/RPO | Approve recovery priorities and customer continuity expectations | ARCHITECTURE IMPLEMENTED / DRILL REQUIRED | Controlled rollback, isolated restore, reconciliation, measured RTO/RPO |
| Payment processing | Keep all external payment processing disabled unless a provider is selected, contracted, implemented, and certified | Select and contract with a provider when ready | DEFERRED BY PRODUCT OWNER | No current implementation work; future provider-specific security, PCI-minimization, webhook, refund, settlement, and reconciliation evidence |

## Product-area control map

| Product area | Sensitive data or risk | Required controls | Current evidence status |
|---|---|---|---|
| Student records and enrollment | Identity, demographics, guardianship, education records | Tenant isolation, role restrictions, correction/export, audit, retention | Source controls substantial; canonical identity reconciliation and runtime proof remain |
| Attendance and academics | Education records, grades, progress | Authorized roles, school scope, audit, parent/student rights support | Module evidence exists; live role and tenant proof remain |
| Health office and emergency data | Health, medication, emergency contacts | Elevated access, minimum necessary use, audit, incident controls | Module evidence exists; detailed access and operational review required |
| Counseling, discipline, pastoral and spiritual-life data | Highly sensitive student information | Elevated RBAC, strict purpose limits, disclosure controls, audit, retention | Module evidence exists; policy and runtime access review required |
| Financial aid and billing | Income, household finances, balances, awards | Elevated roles, ledger integrity, export controls, retention, no external payment activation | Accounting/module controls exist; external processor work deferred |
| Parent, student, teacher and administrator portals | Authentication, role exposure, tenant context | Authenticated sessions, correct role routing, tenant context, least privilege, network/console proof | Authenticated deployed-runtime campaign remains open |
| Communications and documents | Student/family content, attachments, notices | Authorization, malware/content controls where applicable, retention, disclosure audit | Evidence inventory required by feature and storage path |
| Surveys and sentiment | PPRA protected topics, opinions, mental/psychological information | Topic classification, notices, consent/opt-out, purpose limitation, audit | Feature-specific compliance assessment required |
| Analytics and reporting | Aggregation, re-identification, exports | Minimum necessary access, suppression/de-identification where appropriate, export audit | Source/module evidence exists; privacy and export testing required |
| Integrations and Microsoft 365 | Third-party transfer, tokens, identity | Contract/subprocessor review, least privilege, secret management, tenant binding, audit | Architecture exists; production identity and operational evidence remain |

## Required certification packet

CROWN may move from documented readiness to an approved compliance statement only when the packet contains:

1. exact release SHA and deployed identity;
2. current data inventory and classification;
3. approved privacy policy, DPA, and customer responsibility schedule;
4. subprocessor register and contract status;
5. state-law applicability matrix for intended customer jurisdictions;
6. tenant-isolation and cross-school denial evidence;
7. authenticated role and permission evidence;
8. privileged support and break-glass evidence;
9. retention, export, correction, deletion, and backup-expiration evidence;
10. incident-response tabletop or controlled exercise;
11. rollback and restore evidence with measured RTO/RPO;
12. external secret-store, rotation, audit, and revocation evidence;
13. accessibility results and accepted exceptions;
14. legal review disposition;
15. Founder/Product Owner approval.

## Claim boundary

The approved current claim is:

> CROWN has a documented student-data privacy and compliance control framework with substantial repository-level controls. Final runtime, operational, contractual, state-law, and legal validation remains in progress.

This matrix does not certify FERPA, COPPA, PPRA, CIPA, state-law, accessibility, security, pilot, or production compliance by itself.
