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
