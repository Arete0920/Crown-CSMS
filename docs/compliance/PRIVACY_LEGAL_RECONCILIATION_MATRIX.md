# Privacy and Legal Reconciliation Matrix

**Status:** Working reconciliation control; not legal certification.  
**Effective date:** 2026-07-31  
**Last reviewed:** 2026-07-31  
**Repository baseline reviewed:** `d725386a6cfbb48f9967e65e15cd92db27cdfde2`  
**Controlling issue:** #1629 (Lane 5 under #1619)

## Freshness boundary

Before this matrix is used or changed, verify its effective date, repository baseline, controlling issue, active vendor and deployment facts, and whether a later canonical document supersedes it. Older policies, contracts, issue comments, evidence packets, and vendor records are historical unless their current applicability is revalidated.

## Purpose

This matrix defines the evidence that must reconcile repository behavior, runtime operation, written policy, contractual commitments, vendor processing, and buyer-facing claims before production authorization or ownership turnover.

## Evidence dimensions

For every regulated or sensitive data category, the final evidence packet must identify:

| Dimension | Required evidence |
|---|---|
| Data category | Student, parent/guardian, employee, applicant, financial, authentication, disciplinary, attendance, health-adjacent, pastoral, communications, documents, audit, and derived analytics data as applicable |
| Collection | Route, API, form, import, integration, background task, or administrative operation that creates or receives the data |
| Purpose | Documented business and educational purpose, including whether processing is required or optional |
| Storage | Model/table, object storage, logs, caches, artifacts, backups, and external systems |
| Tenant boundary | School/tenant key, query filtering, object authorization, asynchronous context, and cross-tenant denial evidence |
| Access | Authorized personas and privileged operators, including negative tests for unauthorized access |
| Retention | Approved retention period, trigger, exception, legal-hold interaction, backup treatment, and accountable owner |
| Deletion | Executable deletion or de-identification procedure, validation, backup implications, and audit record |
| Export | Authorized requester, identity verification, export scope, delivery protection, audit event, and tenant filtering |
| Legal hold | Hold authority, scope, preservation behavior, release authority, and conflict with deletion requests |
| Audit | Actor, tenant, action, object, timestamp, outcome, retention, and review access |
| Recipient | Internal role, vendor, subprocessor, integration, regulator, or other recipient and transfer purpose |
| Region | Processing and storage region verified from deployed configuration and executed agreement |
| Notice/consent | Applicable notice, consent, authorization, parental/school responsibility, and version evidence |
| Contract | Customer agreement, DPA, vendor agreement, security terms, incident obligations, and allocation of responsibility |
| Incident response | Detection, containment, investigation, notification analysis, evidence preservation, communication, and closure |
| Buyer disposition | Transfer, replacement, consent/notice requirement, continued obligation, or unresolved dependency |

## Current evidence classification

Every matrix row must use one of these binary evidence classifications:

- **IMPLEMENTED AND PROVEN** — current behavior and retained evidence exist for the selected exact SHA or external system.
- **DOCUMENTED ONLY** — a policy or design exists, but operational proof is absent.
- **EXTERNALLY DEPENDENT** — completion requires a vendor, contract, cloud tenant, school decision, or qualified legal review.
- **CONTRADICTED** — repository, runtime, policy, contract, or diligence statements conflict.
- **MISSING** — required control or evidence has not been identified.

Only `IMPLEMENTED AND PROVEN` satisfies an operational control. `DOCUMENTED ONLY` must never be represented as certification.

## Required reconciliation work

1. Complete the repository-bounded processing inventory and trace each category to code and documentation.
2. Verify active production vendors, subprocessors, recipients, and regions from deployed configuration and executed agreements.
3. Map every collection point to notice, consent, authorization, and school/customer responsibility.
4. Prove tenant boundaries and authorized access for records, files, exports, logs, jobs, and integrations.
5. Establish approved retention, deletion, export, legal-hold, and backup-treatment procedures.
6. Exercise deletion and export on representative non-production data and retain validation evidence.
7. Reconcile FERPA-aligned controls and document the applicability and disposition of COPPA, PPRA, state privacy, records-management, and contractual requirements.
8. Exercise the student-data incident procedure through containment, decision, notification analysis, recovery, and evidence retention.
9. Reconcile privacy notices, terms, customer agreements, DPAs, vendor terms, operational practice, and buyer materials.
10. Record qualified legal review disposition for questions requiring legal judgment.

## Blocking contradictions

Lane 5 cannot pass while any critical contradiction exists between product behavior and policy; policy and contract; vendor operation and DPA/subprocessor disclosure; retention statements and executable deletion; incident promises and operational capability; or buyer claims and retained evidence.

## Required final outputs

- completed data-processing matrix;
- verified vendor/subprocessor/recipient register;
- retention and deletion schedule;
- data-subject/school export procedure;
- legal-hold procedure;
- incident-response runbook and exercise evidence;
- policy/contract/product contradiction register with disposition;
- qualified legal review record where required;
- buyer-transfer privacy and contractual obligations register.

## Closure boundary

This document defines the reconciliation method. It does not establish compliance, legal advice, executed agreements, vendor verification, or production readiness. Lane 5 remains open until the completed evidence and legal-review dispositions are linked to #1629 and #1619.
