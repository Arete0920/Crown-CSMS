# CROWN Security Operating Policy

**Status:** DRAFT PROCEDURES COMPLETE / ADOPTION AND OPERATING EVIDENCE OPEN  
**Version:** 1.0  
**Prepared:** 2026-10-07  
**Accountable role:** Founder/Product Owner; actual assignments and delegates must be recorded  
**Approval record:** Not recorded  
**Review cadence:** Annual, after material changes, and following material incidents

## 1. Information security governance

Protect the confidentiality, integrity, and availability of customer and company information. Cover the CROWN service boundary, enabled Diadem services, administrative devices, personnel, repositories, deployments, infrastructure, integrations, and relevant vendors. Final scope requires an approved system description and reconciled inventories.

Management assigns actual control owners, resources, deputies, and review responsibilities. Review the readiness register monthly; record deficiencies, remediation owners/dates, risk decisions, and overdue escalation. No control is complete without the evidence required by the SOC 2 readiness plan. Solo-maintainer authorization must be described accurately and must not be represented as independent approval.

This is a consolidated draft for the twelve policy domains below. Adopt it only after management records approval, scope, actual owners, effective date, next review date, and workforce acknowledgments. Existing release authority and stricter technical controls remain controlling; this draft cannot weaken them.

## 2. Risk management

Assess risks annually and before material service, vendor, data, or infrastructure changes. Identify asset/data, threat scenario, existing verified controls, impact, likelihood, treatment, owner, due date, and residual risk. Consider fraud, insider misuse, vendor failure, credential compromise, cross-tenant disclosure, data loss, and key-person dependency.

Proposed scoring: likelihood 1-5 from unlikely to highly likely; impact 1-5 from limited disruption to severe harm to students, privacy, finance, or essential operations. Record the evidence and uncertainty supporting each score; score is likelihood times impact. Proposed bands: 1-4 low, 5-9 moderate, 10-16 high, 17-25 critical. Credible active compromise or cross-tenant exposure receives immediate incident escalation regardless of score.

Select mitigation, avoidance, transfer, or explicit residual-risk acceptance. Acceptance requires accountable-owner signature, rationale, compensating controls, expiry, and review. No acceptance waives law, customer obligations, or required release gates. These scoring conventions are proposals, not a completed or accepted risk assessment.

## 3. Access control

Maintain a roster of workforce/vendor identities and permissions. Approve access before grant; use named accounts, MFA for privileged/administrative access, least privilege, and tenant scope. Record role changes and promptly remove obsolete privileges. On termination or compromise, revoke accounts, sessions, tokens, and provider access immediately and verify revocation.

Review privileged access monthly and all workforce access quarterly against the complete roster. Record population, reviewer, findings, removals, exceptions, and evidence. Establish physical/device controls appropriate to actual work locations; cloud-provider assurances do not cover unmanaged workforce endpoints.

Customer-content access follows [Support Access Policy](SUPPORT_ACCESS_POLICY.md), including ordinary approval, emergency basis, expiration, revocation, and sensitive-data restrictions.

## 4. Secure development and change management

Use version control, reviewable changes, required exact-head checks, and recorded release identity. Retain relevant security, dependency, tenant, schema, build, test, and approval evidence. Use synthetic fixtures; prohibit customer records or credentials in public source history.

For material changes, record threat analysis covering authorization, tenant scope, inputs, exports, integrations, and data lifecycle. Record emergency changes with incident linkage, scope, actor, validation, rollback, and retrospective review. Do not bypass a failing required gate. Verify the deployed identity separately from source checks.

## 5. Vulnerability and patch management

Maintain software/dependency inventories and recurring scans of the selected deployed environment; source scans alone are insufficient. Triage new findings daily when operating, linking affected assets, severity, exploitability, exposure, and remediation evidence.

Proposed service targets after triage: immediate containment for credible active exploitation; critical remediation within 48 hours; high within 7 calendar days; moderate within 30 days; low within 90 days. Record actual detection and triage times. A release with unresolved critical/high findings remains subject to existing fail-closed release rules regardless of these targets.

Exceptions require owner, reason, compensating measures, expiry, and retest; track overdue work. Verify remediation by rescan and relevant regression checks.

## 6. Vendor and subprocessor management

Before enablement, record the actual legal vendor, service, data categories, regions, permissions, security assurance, contract/DPA, incident terms, retention/deletion, customer notice, and owner. Determine relevant vendor report scope and customer responsibilities rather than inheriting the vendor's assurance.

Review at least annually and after material vendor changes. Review termination, data return/deletion, credential revocation, and continuity alternatives. A candidate integration or library does not establish an active or approved subprocessor. The [subprocessor register](SUBPROCESSOR_REGISTER.md) defines the current evidence boundary.

## 7. Data classification and handling

Maintain field/domain-level inventory and data flows. Classify public, internal, confidential, and restricted information. Treat identifiable student, family, health, counseling, pastoral, discipline, aid, household-finance, identity, and authentication information as restricted unless a reviewed classification establishes otherwise.

Require authorized purpose, minimization, tenant restrictions, secure transmission/storage, controlled exports, and approved recipients. Mask diagnostics and restrict attachments. Do not use student information for sale, behavioral advertising, unrelated profiling, or unapproved external guidance. Removal of names alone does not prove de-identification.

## 8. Retention and deletion

Use [RETENTION_POLICY.md](RETENTION_POLICY.md) as the sole repository retention-control authority. Its defaults do not establish legally approved production periods. Approve each data-class schedule, purpose, minimum/maximum, trigger, jurisdiction, hold, backup treatment, owner, and review date.

Verify school-controlled export/correction/deletion requests and record outcomes. Apply legal holds and approved model-specific lifecycles. Do not run destructive retention commands as part of document preparation or readiness scoring. Coordinate restored data with deletion records before live reuse.

## 9. Encryption and key management

Require approved secure transport and encryption at rest for restricted production records and backups before declaring the corresponding control verified. Inventory keys, secret stores, identities, permissions, rotation, audit, and recovery dependencies without recording secret values.

Follow [Production Secrets Architecture](../security/PRODUCTION_SECRETS_ARCHITECTURE.md) for identity-based external secret storage, workload separation, and evidence. Restrict human administration, test denied access, exercise rotation/revocation and emergency recovery, and retain sanitized proof. Templates and simulation inputs do not prove deployed configuration.

## 10. Logging and monitoring

Inventory log sources, essential security events, delivery paths, retention, access, integrity protection, alerts, and accountable responders. Cover authentication, privileged changes/support, sensitive exports, tenant anomalies, deployment/configuration, backup failure, and enabled integrations. Exclude secrets and minimize unnecessary record content.

Proposed operating cadence: continuous collection/alerting, daily security/backup alert review, and monthly coverage review. Test alert delivery and responder escalation before production acceptance; record actual timestamps and coverage gaps. Verify logs cannot be altered by ordinary application/support identities. Approve storage and retention consistent with the data schedule and contracts.

## 11. Privacy and student data

Use the [Student Privacy and Data Protection Program](STUDENT_PRIVACY_DATA_PROTECTION_PROGRAM.md), FERPA/COPPA positions, approved notices, and executed customer terms. Determine applicability per customer, experience, age, data, and jurisdiction. Keep operator obligations with the operator; school authorization is not a transfer of CROWN's COPPA responsibility.

Verify purpose restrictions, authorization/consent, restricted features, rights workflows, subcontractors, and notification requirements before relevant activation. Health integrations and payment activation retain their separate acceptance requirements.

## 12. Workforce security and training

Before access, verify the actual worker/contractor relationship, confidentiality obligations, assigned role, acceptable-use acknowledgment, and security/privacy training. Apply legally appropriate screening based on role and risk.

Training covers phishing, credentials/MFA, student privacy, public-repository restrictions, tenant/support access, approved tools, incident reporting, retention, and secure devices. Repeat annually and after material role/policy changes. Record training content/version, completion, learner identity, assessment, acknowledgment, and exceptions.

## 13. Acceptable use

Use managed or approved devices with encryption, locking, updates, and access controls. Prohibit shared credentials, unmanaged customer-data copies, unauthorized applications, public disclosure, and personal-account transfers of restricted data. Report lost devices, suspected phishing, and unauthorized access through verified private channels.

Approve external tools and their data handling before use. Do not enter customer/student records, credentials, or sensitive attachments into unapproved support, analytics, or guidance services. Return company/customer materials and revoke access on separation.

## 14. Linked incident and recovery procedures

Incident response is governed by [INCIDENT_RESPONSE_POLICY.md](INCIDENT_RESPONSE_POLICY.md). Continuity and recovery are governed by [BACKUP_RESTORE_POLICY.md](BACKUP_RESTORE_POLICY.md). Their response/recovery targets require adoption and measured exercises. Record recovery deputies and key-person coverage.

## 15. Evidence and completion

Maintain dated approvals, inventories, review populations, tests, training, vendor reviews, incident/recovery exercises, exceptions, and corrective-action verification in restricted evidence storage. Proposed evidence retention is at least 12 months, extended for contracts, holds, or the auditor-agreed observation period.

A draft is not an adopted policy; an adopted policy is not operating proof; a completed readiness assessment is not a CPA report or ISO certificate. Apply the separate evidence states in [SOC2_READINESS_PLAN.md](SOC2_READINESS_PLAN.md).
