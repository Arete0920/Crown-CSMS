# Crown Privacy and Compliance Operating Framework

## FERPA / COPPA Compliance Documentation

Effective Date: July 1, 2026

## 1. Scope and Purpose

This document defines Crown's operating framework for compliance with FERPA and COPPA.
Crown operates as a school official under FERPA and processes student data only under
the direction of partner schools.

## 2. Roles and Responsibilities

| Role | Responsibility |
|---|---|
| Partner School | Data controller and owner of student records |
| Crown | Data processor and school official |
| Crown Compliance Officer | Internal policy owner and incident coordinator |
| School Data Administrator | School-side point of contact for FERPA requests |

## 3. Data We Process

| Category | Examples | Retention |
|---|---|---|
| Student identity | Name, date of birth, grade level, student ID | Enrollment duration plus 7 years |
| Academic records | Grades, attendance, transcripts | Enrollment duration plus 7 years |
| Financial records | Billing amounts, payment history, aid applications | 7 years |
| Family records | Guardian contacts, household structure | Enrollment duration plus 7 years |
| Faith records | Chapel attendance, Bible progress, milestones | Enrollment duration |
| Communications | Announcements and messages | 2 years |
| Audit logs | Access and change logs | 7 years |

## 4. Access Controls

- Student data is scoped to the owning school.
- Access within a school is governed by RBAC.
- API endpoints require authentication.
- Audit logs are written for sensitive mutations.

## 5. Data Subject Rights

School administrators can inspect, correct, export, and request deletion of student records.

## 6. Data Processing Agreement

Every partner school must execute Crown's DPA before onboarding.

## 7. Sub-Processors

| Sub-Processor | Purpose | Data Shared |
|---|---|---|
| Microsoft Azure | Cloud infrastructure | Platform data |
| CompuWerx | Payment processing | Billing amounts and transaction metadata |
| Sentry | Error monitoring | Error traces and request metadata |
| Twilio | SMS notifications | Phone numbers and message content |

## 8. Incident Response

| Phase | SLA | Owner |
|---|---|---|
| Detection | Within 4 hours of alert | Crown DevOps |
| Containment | Within 24 hours | Engineering lead |
| School notification | Within 72 hours of confirmed breach | Compliance officer |
| Post-incident review | Within 14 days | Engineering and compliance |

## 9. COPPA Applicability

Crown serves K-12 schools and operates under the school-consent exception for COPPA.

## 10. Compliance Contacts

| Purpose | Contact |
|---|---|
| Security incidents | security@crownschoolsystem.com |
| DPA execution and legal | legal@crownschoolsystem.com |
| General compliance | compliance@crownschoolsystem.com |