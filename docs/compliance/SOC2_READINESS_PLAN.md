# CROWN SOC 2 Readiness Plan

**Status:** Pre-audit readiness plan  
**Primary target:** SOC 2 Type I readiness, followed by Type II observation period  
**Initial Trust Services scope:** Security  
**Candidate additional categories:** Availability, Confidentiality, Processing Integrity, Privacy

## Objective

Prepare CROWN for an independent SOC 2 examination by converting existing engineering controls into documented, repeatable, evidenced organizational controls.

## Phase 1 — Define scope

- identify the legal entity and service organization covered by the report;
- define in-scope CROWN products, modules, infrastructure, people, vendors, and locations;
- define production architecture and system boundaries;
- identify customer commitments and system requirements;
- determine whether Security-only or additional Trust Services categories are appropriate;
- establish control owners and an evidence repository.

## Phase 2 — Build the control environment

Required governance artifacts:

- Information Security Policy
- Access Control Policy
- Secure Development / Change Management Policy
- Vulnerability and Patch Management Policy
- Incident Response Plan
- Business Continuity / Disaster Recovery Policy
- Vendor / Subprocessor Management Policy
- Data Classification and Handling Policy
- Data Retention and Deletion Policy
- Encryption and Key Management Standard
- Logging and Monitoring Standard
- Risk Management Policy
- Privacy and Student Data Policy
- Workforce Security and Training Policy
- Acceptable Use Policy

## Phase 3 — Evidence existing technical controls

Evidence should include:

- authentication/MFA settings;
- RBAC and privileged-role definitions;
- tenant-isolation tests;
- CodeQL/static-analysis results;
- dependency and vulnerability scan results;
- secret-scan results;
- CI branch/release controls;
- pull-request and code-review evidence;
- production configuration and secure headers;
- database TLS/encryption evidence;
- audit logs and monitoring alerts;
- backup and restore results;
- incident records and tabletop exercises;
- access-review records;
- vendor reviews and contracts.

## Phase 4 — Privacy / education-data operationalization

Create and approve:

- CROWN Data Processing Addendum;
- Student Data Privacy Addendum;
- FERPA-aligned school-official / outsourced-service terms;
- COPPA school-authorization and parent-consent procedures;
- parent/student data-access and correction workflow;
- deletion/return-of-data procedure;
- subprocessor list and change-notification process;
- incident/breach notification procedure;
- data-retention schedule;
- restricted health/student-support data controls;
- state-law addendum matrix.

## Phase 5 — Readiness assessment

Perform a gap assessment against each in-scope criterion and classify each control:

- Designed and evidenced
- Designed but evidence insufficient
- Partially designed
- Missing
- Not applicable

Every control must have:

- control objective;
- owner;
- frequency;
- procedure;
- evidence source;
- exception handling;
- retention period.

## Phase 6 — Type I

Engage an independent CPA firm to examine whether controls are suitably designed and implemented as of a specified date.

Do not market CROWN as SOC 2 compliant or SOC 2 certified merely because readiness work is complete.

## Phase 7 — Type II

After controls are operating consistently, enter an observation period and retain recurring evidence of control operation for the auditor's examination of operating effectiveness.

## Release rule

Compliance-readiness documentation does not override engineering release gates. Production release continues to require exact-head security, test, dependency, tenant, schema, build, and release evidence.

## Execution baseline — 2026-10-07

**Disposition:** Readiness in progress; no independent report, completed readiness assessment, policy approval, or production exercise is asserted.

### Scope decision record

Proposed service organization: Arete Advisory Group LLC operating CROWN. Confirm legal entity, contracting entity, and ownership against authoritative corporate records before auditor acceptance. Include Diadem only after its actual service/infrastructure boundary is documented. Engineering, administration, support, workforce devices, CI/CD, hosting, databases, storage, identity, communications, logging, and subprocessors affecting the service must be evaluated.

Initial candidate category is Security. Decide additional categories against customer commitments with the CPA; do not omit security-relevant systems merely because a separate category is excluded. Identify each disabled module/integration and its activation gate. Current payment activation remains prohibited by the current release authority.

Required scope decisions remain OPEN: production provider/environment and regions; system description; named control owners and deputies; workforce/vendor population; complete data flows; customer commitments; subservice-organization treatment and complementary controls; assessment date/period; evidence repository; auditor engagement. No hosting provider assurance is inherited automatically by CROWN.

### Governance and evidence procedure

The Founder/Product Owner is the proposed accountable executive, subject to a recorded assignment. Engineering/Operations, Privacy/Legal, and School Success are proposed operating roles, not assertions of hired staff. Record actual people, delegates, and conflicts before closing ownership.

For each control, maintain: objective; applicable criterion; scope; named owner; approved procedure/version; cadence; population; evidence reference; UTC capture time; environment and source SHA where relevant; reviewer; test result; exception; remediation due date; and closure approval. Evidence must be access-controlled and retained for an approved period. Proposed baseline is 12 months, extended for the auditor-agreed observation period, contracts, or holds. Customer personal information and secrets must not enter the public repository.

Collect the complete population where feasible; otherwise record the population, sampling method, sample, and rationale. A screenshot or passing source test cannot substitute for the specific runtime, contract, or recurring operating evidence required.

### Control execution register

These mappings are preliminary Common Criteria family mappings for readiness planning, not an exhaustive criterion-level auditor assessment. Expand each family to applicable individual criteria with the CPA before readiness closure. Cadences below are proposed policy requirements until approved.

| ID | Preliminary mapping | Required control and evidence | Proposed accountable role | Cadence | Initial disposition |
| --- | --- | --- | --- | --- | --- |
| S01 | CC1 | Security accountability, ethical conduct, competence, oversight, role assignments and acknowledgments | Founder/Product Owner | Annual and role change | OPEN: approval/people evidence |
| S02 | CC2 | System description, information quality, customer commitments and internal/external communication records | Founder/Product Owner | Material change and annual | OPEN: scope/communication evidence |
| S03 | CC3 | Documented risk assessment, fraud/change risk, treatment and residual-risk decisions | Founder/Product Owner | Annual and material change | OPEN: assessment/acceptance |
| S04 | CC4 | Control review, deficiency tracking, corrective-action verification | Founder/Product Owner | Monthly readiness review | OPEN: operating review |
| S05 | CC5 | Approved policies, technology control ownership and exception process | Founder/Product Owner | Annual and material change | OPEN: approvals |
| S06 | CC6 | Complete asset, software, data and workforce inventories reconciled to actual deployment | Engineering/Operations | Monthly and material change | OPEN: production population |
| S07 | CC6 | Named accounts, MFA, least privilege, joiner/mover/leaver and access recertification | Engineering/Operations | Event-driven; monthly privileged; quarterly all | OPEN: live evidence |
| S08 | CC6 | Tenant isolation and restricted support access, including grant/revoke and break-glass tests | Engineering/Operations | Each relevant release and access event | OPEN: deployed proof |
| S09 | CC6 | Provider physical-access assurance and customer device/storage safeguards | Engineering/Operations | Annual vendor review and change | OPEN: provider/device evidence |
| S10 | CC6 | Encryption, key custody/rotation, secure transmission and disposal | Engineering/Operations | Continuous configuration; quarterly review | OPEN: production proof |
| S11 | CC7 | Vulnerability discovery, severity SLAs, triage, remediation and exception history | Engineering/Operations | Each relevant release; recurring production scan | OPEN: current population/SLA approval |
| S12 | CC7 | Central security logs, protected retention, alert routing and response coverage | Engineering/Operations | Continuous; daily alert review | OPEN: deployed alert test |
| S13 | CC7 | Incident classification, containment, notification and post-incident review | Founder/Product Owner | Each incident; annual tabletop | DRAFT_COMPLETE: incident policy; exercise open |
| S14 | CC7 | Backup coverage, failure alerts and measured recovery/reconciliation | Engineering/Operations | Daily backups; quarterly sampled restore; annual full exercise | DRAFT_COMPLETE: recovery policy; exercise open |
| S15 | CC8 | Reviewed changes, protected release controls, emergency changes and exact deployed identity | Engineering/Operations | Each change/release | OPEN: exact-head and deployment evidence |
| S16 | CC9 | Vendor/subprocessor risk, contracts, monitoring and continuity alternatives | Founder/Product Owner | Before onboarding; annual and material change | OPEN: actual vendors/contracts |
| S17 | CC1, CC2, CC6 | Workforce security/privacy training, confidentiality and acceptable use | Founder/Product Owner | Before access; annual and role change | OPEN: completed acknowledgments/training |
| S18 | CC2, CC6, CC9 | Privacy notices, customer terms, purpose limits and consent applicability | Privacy/Legal | Before customer activation and material change | OPEN: approved terms/workflows |
| S19 | CC6, CC7 | Retention, legal hold, deletion/export and restored-data safeguards | Engineering/Operations | Each request; annual exercise | OPEN: approved schedule/test |
| S20 | CC4 | Independent readiness review and unresolved-risk disposition | Founder/Product Owner | Before readiness claim | OPEN: reviewer findings |
| S21 | All in-scope | Type I CPA examination/report at specified date, if selected | Independent CPA | Auditor-agreed date | EXTERNAL_PENDING |
| S22 | All in-scope | Type II recurring evidence and CPA examination/report, if selected | Independent CPA | Auditor-agreed period | EXTERNAL_PENDING |

Draft operating procedures: [Incident response](INCIDENT_RESPONSE_POLICY.md), [Support access](SUPPORT_ACCESS_POLICY.md), and [Backup/restore](BACKUP_RESTORE_POLICY.md). They replace placeholders but do not establish approval or operational effectiveness.

### Initial risk triage

Evidence gaps are not confirmed incidents or findings of exploitation. Score actual likelihood and impact during the documented assessment; do not invent scores.

| Risk | Exposure or evidence gap | Treatment required | Owner role | Disposition |
| --- | --- | --- | --- | --- |
| R01 | Customer records exposed across tenants or through privileged support | Deployed tenant/role denial tests, restricted access reviews, logged revocation and break-glass exercise | Engineering/Operations | OPEN |
| R02 | Loss of data or service with unproven recovery | Approved recovery objectives, complete backup inventory, alert test and measured full restore | Engineering/Operations | OPEN |
| R03 | Incident notification missed or delayed | Verified contacts, applicable contract/law matrix and tabletop | Founder/Product Owner | OPEN |
| R04 | Uncontrolled subprocessors or unknown processing locations | Reconcile vendor register to actual deployment, review agreements and regions | Founder/Product Owner | OPEN |
| R05 | Misleading compliance or production claims | Separate documented/design/runtime/operating/external evidence and reconcile public statements | Founder/Product Owner | OPEN |
| R06 | Key-person dependency and conflicting approval roles | Deputies/recovery access, recorded compensating review and continuity exercise | Founder/Product Owner | OPEN |
| R07 | Retention, consent or deletion inconsistent with customer obligations | Approved applicability/retention decisions and lifecycle tests | Privacy/Legal | OPEN |
| R08 | Release or credential compromise | Current source checks, deployment identity, restricted secrets and rotation/access evidence | Engineering/Operations | OPEN |

For each risk, record asset/data, scenario, inherent likelihood/impact, existing verified controls, treatment owner/due date, residual likelihood/impact, acceptance authority, expiry, and review date. Acceptance cannot waive applicable law, contractual obligations, or release gates.

### Completion rules and permitted reporting

- DRAFT_COMPLETE: substantive procedure authored and reviewed for consistency; approval and execution remain open.
- APPROVED: dated management approval and actual owners recorded.
- IMPLEMENTED: identified code/configuration/process exists with evidence.
- VERIFIED: a dated test on the identified environment meets the control objective.
- OPERATING: required recurring activity is evidenced across the chosen period.
- NOT_APPLICABLE: documented scope rationale approved and reviewed; not a shortcut for missing evidence.
- READINESS_COMPLETE: approved scope, exhaustive criterion mapping, every applicable control adequately designed/implemented/evidenced, risk review, and independent readiness findings resolved or appropriately dispositioned. This is not a SOC 2 report.
- REPORT_ISSUED: an independent CPA report is obtained; external statements must specify actual type, scope, date/period, and any qualifications.

Do not calculate a completion percentage from draft documents alone. Report separate counts of documentation, approval, implementation, verification, operation, and external assurance. Documentation merge closes only the drafting task.

### Work sequence

1. Reconcile scope and map all applicable criteria; approve owners and risk methodology.
2. Approve and exercise incident response, support access, and recovery procedures.
3. Complete workforce/access, vendor, asset/data, encryption, monitoring, vulnerability, and change evidence.
4. Complete privacy/contract/consent/retention workflows with qualified review.
5. Conduct the independent readiness assessment; resolve findings; select the CPA engagement and observation period.
6. Obtain the report before representing independent assurance.
7. Proceed to ISO/IEC 27001, FERPA, COPPA, HIPAA applicability, PCI/payment, and remaining jurisdictional obligations using shared verified evidence; each retains its own completion criteria.

Official framework source: [AICPA Trust Services Criteria, 2017 with revised points of focus 2022](https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022).
