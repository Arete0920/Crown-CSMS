# CROWN Regulated and Sensitive Data Inventory

**Status:** CONTROLLED COMPLIANCE SUPPORTING RECORD / PARTIAL SOURCE INVENTORY  
**Effective date:** 2026-07-29  
**Observed source identity:** `93d65d61d1aa205e1ddedbfcd770c7927d7a9f01`  
**Controlling issues:** #1759, #1629, and #1619

## Purpose and boundary

This record inventories regulated and sensitive data evidenced in current repository source. It is intentionally incomplete pending exhaustive model and data-path enumeration under #1759.

It does not establish production data flows, active vendors, processing regions, retention periods, legal applicability, contractual approval, runtime verification, or production authorization.

## Evidence-status rule

- **VERIFIED SOURCE** — current source directly defines the field, relation, storage behavior, or control.
- **PARTIAL** — the domain is confirmed but processing, exports, logs, backups, retention, deletion, or external recipients are not fully mapped.
- **UNVERIFIED** — a likely path or operational behavior requires additional evidence.
- **NOT AUTHORIZED** — functionality remains disabled or outside current scope.

## Verified source domains

| Domain | Data subjects | Verified source data | Primary source | Current status |
|---|---|---|---|---|
| School and academic structure | School personnel, students | School identity, timezone, academic years, grade levels | `backend/core/models.py` | VERIFIED SOURCE / PARTIAL FLOW |
| Family and household | Guardians, parents, students | Family name, street address, city, state, postal code, status | `backend/core/models.py` | VERIFIED SOURCE / HIGH SENSITIVITY |
| Guardian and custody | Guardians, parents, students | Name, email, phone, relationship, portal access, custody flag | `backend/core/models.py` | VERIFIED SOURCE / HIGH SENSITIVITY |
| Student identity | Students | Student number, name, date of birth, status, family and grade relations | `backend/core/models.py` | VERIFIED SOURCE / HIGH SENSITIVITY |
| Staff and authentication | Employees, administrators, support users | Name, email, role, status, user account, school, staff/guardian link, assigned roles | `backend/core/models.py` | VERIFIED SOURCE / AUTHENTICATION SENSITIVE |
| Enrollment and academics | Students, families | Academic year, grade, enrollment dates and status | `backend/core/models.py` | VERIFIED SOURCE / EDUCATION RECORD |
| Tuition and ledger | Students, families, staff users | Tuition amounts, discounts, balances, dates, account/batch relations, memos, source, creating user, reversal links | `backend/core/models.py` | VERIFIED SOURCE / FINANCIAL SENSITIVE |
| Admissions | Applicants, students, families, reviewers | Application status, GPA, test score, essay/transcript/recommendation indicators, internal notes, contact history, academic/character/mission-fit scores, recommendation, decision, audit JSON | `backend/admissions/models.py` | VERIFIED SOURCE / HIGH SENSITIVITY |
| Financial aid | Families, students, approvers | Household income, household size, hardship/mission/merit classifications, award amounts, rationale, approver, audit message | `backend/financial_aid/models.py` | VERIFIED SOURCE / HIGH SENSITIVITY |
| Discipline | Students, families, staff | Incident date/location, bullying/disrespect and other categories, severity, status, narrative summary/details, assigned users, parent notification, action notes | `backend/discipline/models.py` | VERIFIED SOURCE / HIGH SENSITIVITY |
| Spiritual life and pastoral care | Students, staff, families | Faith background, baptism status/date, spiritual gifts, assessments, chapel and small-group attendance, prayer request content and visibility, private pastoral notes | `backend/spiritual_life/models.py` | VERIFIED SOURCE / RESTRICTED SENSITIVE |
| Audit and actor attribution | Users, students, families | Event/action identifiers, actor user, timestamps, entity identifiers, JSON or narrative details | Multiple verified model files | VERIFIED SOURCE / RETENTION OPEN |

## Verified control observations

### Tenant and ownership relationships

Reviewed models commonly include school, student, family, household, user, or actor relationships. These relationships support source-level ownership and tenant-scoping analysis but do not alone prove runtime authorization or complete object-level isolation.

### Deletion behavior

`TenantSafeModel.delete()` blocks hard deletion for tenant-owned models, and ledger entries block deletion in favor of reversals. Other reviewed models use combinations of `CASCADE`, `PROTECT`, and `SET_NULL`.

These are source behaviors, not a complete retention, deletion, anonymization, backup-expiration, or legal-hold procedure. Cascade relationships may delete dependent records when a parent record is deleted; that behavior requires domain-by-domain review before any customer deletion representation.

### High-risk free text and JSON

Confirmed high-risk unstructured fields include:

- ledger memos;
- admissions internal and recommendation notes;
- admissions audit JSON;
- financial-aid rationale and audit messages;
- discipline summaries, details, and action notes;
- spiritual-profile notes, assessment notes, prayer-request bodies, and pastoral-note bodies.

Unstructured fields may contain information beyond the field label and require access, export, logging, retention, redaction, and deletion controls appropriate to their actual use.

### Backup configuration

Current settings define `CROWN_BACKUP_RETENTION_DAYS` with a default of 30 days. This is configuration evidence only. It does not prove the production backup provider, actual retention, tenant-aware deletion propagation, expiration enforcement, restore behavior, or legal-hold handling.

### Payment boundary

The Django app registry includes a payments application, but external payment-provider functionality remains disabled/deferred by controlling authority. This inventory does not infer an active processor or production payment flow.

## Active app-domain coverage requiring exhaustive enumeration

Current settings register a broad application surface including admissions, accounting, finance, financial aid, academics, classroom, gradebook, billing, audit, discipline, communications, student records, HR, advancement, safety, spiritual life, athletics, facilities, transportation, identity, platform operations, subscriptions, support, analytics, aftercare, summer camp, and home academy.

The following remain incomplete until Codex machine enumeration is reconciled:

- every concrete Django model and field;
- database table and relation graph;
- upload/file fields and object-storage paths;
- export and report generation;
- email, SMS, notification, and communication payloads;
- audit, security, application, and analytics logs;
- browser storage and cookies;
- backup and restore propagation;
- deletion, anonymization, purge, and legal-hold paths;
- external integrations and recipients;
- production versus sandbox handling;
- data owner and system of record by domain.

## Required processing-map dimensions

Each final inventory entry must identify, where evidenced:

1. data subject;
2. collection source;
3. processing purpose;
4. model, table, file, browser, log, or backup storage path;
5. tenant, school, household, student, and role boundary;
6. internal recipients and privileged access;
7. exports and generated artifacts;
8. external recipients and subprocessors;
9. production and non-production handling;
10. retention trigger and period;
11. correction, return, deletion, anonymization, backup-expiration, and legal-hold path;
12. audit events and accountable owner;
13. evidence level and unresolved gaps.

## Closure boundary

This partial record does not satisfy #1629 or #1759. Completion requires reconciliation of the exhaustive Codex enumeration, review of data paths outside Django models, explicit unknowns, and an evidence-backed processing map. Operational, contractual, jurisdiction-specific, and legal work remains separate.

Production remains **NOT APPROVED / NO-GO / HOLD**.
