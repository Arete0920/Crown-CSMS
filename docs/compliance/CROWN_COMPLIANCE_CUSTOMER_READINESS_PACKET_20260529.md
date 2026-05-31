# CROWN Compliance and Customer-Readiness Packet — 2026-05-29

## Decision

**DOCUMENTED, NOT LEGAL-SIGNED.**

This packet closes the repository-documentation gap for compliance/customer-readiness content. It does not replace legal counsel review, customer-specific DPA negotiation, security review, or founder/product-owner final acceptance.

## Scope

CROWN handles school operations data involving students, families, staff, communications, billing, health-office workflows, academic records, student care, and school operations. All such data must be treated as confidential school-controlled data unless explicitly classified otherwise by the school customer and applicable law.

## Reference law and guidance baseline

- FERPA: U.S. Department of Education, 34 CFR Part 99, Family Educational Rights and Privacy.
- FERPA education records: records directly related to a student and maintained by an educational agency/institution or a party acting for it.
- FERPA personally identifiable information includes student/parent/family names, address, personal identifiers, indirect identifiers, and linkable information.
- COPPA: FTC Children's Online Privacy Protection Rule and FTC business guidance for child-directed or under-13 online services.

## Policy positions

### 1. FERPA position

CROWN is designed to act as a school-directed service provider and processor for school operations records. Schools remain the authoritative data owners/controllers for education records. CROWN must process student education records only for legitimate school purposes defined by contract, school configuration, and authorized user roles.

Required controls:

- Access is role-based and tenant-scoped.
- School officials and support personnel receive only minimum necessary access.
- Disclosure/export actions are logged.
- Parent/student access follows the school's configured rights, notices, and legal obligations.
- Directory information is not assumed public by default.
- Cross-tenant disclosure is treated as critical.
- Education-record exports require authorization and audit logging.

### 2. COPPA position

CROWN is not a consumer social product. CROWN is a school operations platform configured for use under school direction. For any features directed to children under 13 or knowingly used by children under 13, CROWN must use a school-consent/parent-consent model consistent with the customer's legal basis and contract.

Required controls:

- No behavioral advertising to students.
- No sale of student data.
- No unrelated profiling of students.
- Child/student data collection is limited to school-operational purposes.
- Parent-facing notices must describe student-facing data flows where applicable.
- Under-13 direct account access must be school-approved and tenant-configured.
- Student data deletion/export requests route through the school-controlled process unless law or contract provides otherwise.

### 3. Data Processing Addendum template position

Every production customer must have an executed agreement or order form incorporating a DPA before production data is loaded.

Minimum DPA terms:

- Customer data ownership remains with the school/customer.
- CROWN processes data only for contracted services.
- No sale or advertising use of student data.
- Confidentiality obligations for personnel and subprocessors.
- Security controls, access controls, encryption, backup, incident notification, and deletion/return obligations.
- Subprocessor disclosure and update process.
- Audit/cooperation commitments.
- Data location and retention terms.
- FERPA/COPPA/student-data privacy support terms.

### 4. Data retention policy

Default retention posture:

- Active customer data is retained for the term of service.
- Deleted records are soft-deleted where operationally required for audit, reconciliation, transcript, billing, or compliance purposes.
- Hard deletion, anonymization, or export-return follows contract, law, and customer instruction.
- Backups are retained only for documented restore windows.
- Logs containing personal data are minimized and rotated.
- Demo/sandbox data must not include real student/family/staff/financial/health data.

Required implementation evidence:

- Data inventory by model/domain.
- Retention class per model/domain.
- Deletion/anonymization procedure.
- Backup retention schedule.
- Restore test evidence.
- Audit log retention schedule.

### 5. Support access policy

Support access to customer data must be least-privilege, time-bounded, approved, and audited.

Required controls:

- No standing unrestricted support access.
- Support access requires school/customer approval or documented emergency/break-glass reason.
- All support impersonation or privileged access is logged.
- Support personnel cannot export bulk data unless authorized.
- Break-glass access triggers post-event review.
- Sensitive student care, health, counseling, discipline, and financial aid data require elevated restrictions.

### 6. Incident response policy

CROWN incident response must cover suspected unauthorized access, cross-tenant exposure, credential compromise, data loss, service outage, ransomware/malware, subprocessor incident, and accidental disclosure.

Required phases:

1. Detect and triage.
2. Preserve logs/evidence.
3. Contain exposure.
4. Assess affected tenants, users, records, and data categories.
5. Notify internal owner and customer contacts under contractual timelines.
6. Remediate root cause.
7. Validate closure.
8. Produce incident report and lessons learned.

Cross-tenant exposure is severity critical until disproven.

### 7. Subprocessor register policy

Production CROWN must maintain a current subprocessor register listing each service provider that may process customer data.

Minimum register fields:

- Vendor name.
- Service purpose.
- Data categories processed.
- Processing location/region when known.
- Security/compliance notes.
- Contract/DPA status.
- Customer notice/change process.

No production customer data may be processed by an unregistered subprocessor unless emergency processing is documented and approved under incident/change control.

### 8. Backup and restore policy

Production readiness requires backup and restore proof, not only backup configuration.

Required controls:

- Automated backups for production databases and critical files.
- Backup encryption.
- Tenant-aware restore procedure.
- Restore test evidence before GA/pilot approval.
- Documented RPO/RTO targets.
- Backup access restricted to authorized operations/security personnel.
- Backup deletion/expiration aligned with retention policy.

### 9. Sandbox/no-real-data policy

Sandbox environments must use only synthetic, test, or clearly authorized non-production data.

Required rules:

- No real student data.
- No real family data.
- No real staff data unless specifically approved for a controlled test under written authorization.
- No real school financial data.
- No production secrets.
- No production database dumps.
- Sandbox credentials must not be committed.
- Demo/sample data must be labeled and must never be certified as production-live evidence.

### 10. Controlled pilot entry criteria

Pilot may begin only after:

- Current release gates are green.
- Tenant isolation proof is green.
- RBAC/permission proof is green.
- Compliance packet is approved.
- Backup/restore proof is complete.
- Support access policy is active.
- Incident response contacts/process are active.
- Sandbox data rules are enforced.
- Pilot school scope, users, modules, data categories, success criteria, and rollback plan are written.
- Founder/Product Owner signs pilot entry.

### 11. Controlled pilot exit criteria

Pilot may exit to GA only after:

- No unresolved critical/high security or data-integrity incidents.
- No unresolved cross-tenant, RBAC, or privacy blocker.
- All scoped pilot workflows pass real user acceptance.
- Backup restore has been tested during pilot window or immediately before exit.
- Support process metrics are reviewed.
- Data accuracy/reconciliation is accepted by pilot school.
- Accessibility/responsive blockers are closed or explicitly accepted.
- Final release authority signoff is executed.

## Open proof requirements after this packet

This packet supplies policy content. The following still require execution evidence:

- Legal review/approval.
- Customer DPA finalization.
- Subprocessor register population with actual vendors.
- Backup restore test.
- Incident-response tabletop or test.
- Support-access audit proof.
- Runtime enforcement proof.
- Founder/Product Owner final acceptance.

## Status

Policy packet: **DOCUMENTED**

Certification impact: **NOT GREEN until legal/signoff/runtime evidence is attached.**
