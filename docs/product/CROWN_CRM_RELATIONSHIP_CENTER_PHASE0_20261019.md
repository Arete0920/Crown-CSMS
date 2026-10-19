# CROWN Relationship Center — Phase 0 Baseline, Gaps and Delivery Gates

**Status:** PROPOSED DESIGN SPECIFICATION — not an implemented product, certified release, or accepted ADR
**Date:** 2026-10-19
**Repository:** Arete0920/Crown-CSMS
**Source baseline inspected:** accepted main 433aa0b6cb54c3b5a86f50f5f3137c46ebb12940
**Proposed architecture:** [ADR-0006](../architecture/decisions/ADR-0006-crm-relationship-domain-boundaries.md)
**Scope of this file:** source-observed CRM work, bounded design choices, risk disposition, next implementation slices and acceptance tests.

## 1. Objectives and exclusion

Deliver a tenant-safe school relationship center covering prospective families, admissions, active-family engagement, staff work, church/community referrals, and permissioned alumni/advancement projections. Do not build a separate Arete B2B vendor sales CRM on school-owned family data. Do not duplicate canonical SIS, ledger, donor or communications records. Do not deploy, activate messaging, or modify data under this design-only slice.

## 2. Existing foundation observed in accepted source

| Area | Source evidence | Classification |
| --- | --- | --- |
| School-scoped leads, stages, campaigns, touchpoints | backend/crm_marketing/models.py; migrations 0001, 0002 | Implemented source; runtime not inferred |
| Public intake and idempotent replay | api/inquiries.py, inquiry_services.py, admissions API contract | Implemented source; hosted verification separate |
| Pre-application continuation, multi-application linking | inquiry_services.py, applications/views_admissions.py | Implemented source, preserve contract |
| Protected admissions queue and ownership | frontend/dashboards/src/pages/AdmissionsInquiryQueue.jsx, api/inquiries.py | Implemented source |
| Consent-aware reminder task + outbox guard | crm_marketing/tasks.py, inquiry_notifications.py, comms/models.py | Implemented source; notifications default off, provider delivery unverified |
| Campaign conversion and estimated economics | crm_marketing/services.py, crown_api/metrics_views.py | Implemented source; estimated != actual receipts |
| Advancement donor/relationship/prospect/move | advancement/models.py, models_stage3.py | Existing separate domain; not CRM write authority |
| Canonical family/guardian/student operational identity | docs/architecture/ADR-001-CANONICAL-HOUSEHOLD-GUARDIAN-STUDENT.md | Accepted Core authority |
| Legacy household/person model convergence | docs/architecture/IDENTITY_MODEL_CONVERGENCE_LEDGER.md | Not complete; no silent identity rewrite |
| Authenticated protected browser transport | docs/architecture/ARCHITECTURE_MAP.md; ADR-0002 | Accepted transport authority |
| Dedicated CRMTask / ProspectGroup / EnrollmentInterest / VerifiedIdentityLink | Search of accepted source for candidate model names | Not identified in checked code search; requires complete model inventory before asserting absence platform-wide |
| Hosted CRM E2E/provider execution at exact release identity | Accepted source alone | Not established |

## 3. Findings and decisions

### F-01: Family aggregate stage can regress (critical)

Current main crm_marketing.services.register_admissions_submit and register_workflow_update update MarketingLead.stage from one application. With multiple child applications linked to one lead, a sibling's later transition can overwrite a prior confirmed enrollment. Draft PR #353 proposes a targeted preservation correction on the inspected main; it is not merged or tested by this documentation PR. **Disposition:** Do not duplicate #353. Check exact final tests, accepted merge and authoritative enrollment-stage derivation before implementing separate opportunity stages.

### F-02: Identity models conflict unless authority is explicit (critical)

Historical inventory docs have inconsistent claims, but the accepted ADR index and ADR-001 assign core.Family, core.Guardian, core.Student operational writes. households and crown_api person/household sets remain compatibility domains with a convergence ledger. **Disposition:** CRM owns only provisional contacts/groups until reviewed links to Core; never auto-merge or migrate records by matching contact details. Existing admissions compatibility writes require a separate scoped review before any new identity integration.

### F-03: One lead does not model each school-interest opportunity (high)

MarketingLead has grade_interest and entry_year on a lead plus one compatibility application FK and multi-application link. Multiple children/years require a child-level interest model and separate stage calculation. **Disposition:** Proposed EnrollmentInterest is additive and points to canonical applications only after verified relation.

### F-04: Inquiry list query/cap behavior can limit scale (high)

The protected GET leads query hard-caps serialized results at 100 and invokes per-lead duplicate candidate and notification status lookups in _serialize. It returns a match count but no cursor/offset contract in the inspected source. **Disposition:** Introduce bounded, deterministic pagination and batched status/duplicate projections, with query-count and response-contract regressions; preserve historical response compatibility.

### F-05: Messaging and consent are narrow by design (critical)

The existing receipt captures response consent and optional follow-up consent; staff may withdraw but not grant. Notification enqueue and provider delivery remain explicitly gated; API exposes not-enabled truth. **Disposition:** Maintain gate default off, model consent by purpose/channel before expanding marketing messaging, and test withdrawal after queueing and immediately before send. No enabled live sends as part of CRM features.

### F-06: CRM touchpoints and advancement relationship histories overlap semantically (high)

CampaignTouchpoint and advancement.Move/Relationship are valid separate records in their respective domains; a new global interaction store could accidentally duplicate canonical histories. **Disposition:** Retain source histories and construct a read-only, permission-filtered timeline; postpone CRMInteraction writer until ownership/migration decision is approved.

### F-07: Metrics must not mix family, child and financial units (high)

Existing metrics explicitly distinguish family inquiry counts and linked child applications. Campaign estimated tuition, aid and conversion values are not verified billing/ledger receipts. **Disposition:** Every KPI declares population, unit, date window, source and whether authoritative/estimated/demo; no misleading aggregate sums.

### F-08: Staff permissions and sensitive data separation (critical)

Admissions, marketing and advancement use separate permissions. A consolidated 360 UI can leak child welfare, faith/pastoral, custody, disability, financial aid or billing information if it simply joins every table. **Disposition:** Whitelist fields by CRM permission and originating domain; enforce in backend adapters and exports, not just hide in React.

### F-09: Existing marketing dashboard template includes illustrative constants (medium)

The dashboard template includes static metrics and trends and labels itself a launch preview even while referencing a live API endpoint. **Disposition:** Separate preview fixtures from live rendering; add "unavailable" state on missing authoritative metrics. No forged real-time counts.

## 4. Proposed domain data contract

Entities are intentionally candidates, not approved migrations.

| Entity | Immutable or unique business identity | Tenant and relational rule | Source owner |
| --- | --- | --- | --- |
| ProspectContact | UUID; no email-based global uniqueness | school_id; any duplicate-resolution same school and reviewed | CRM |
| ProspectGroup | UUID | school_id; no automatic core.Family creation | CRM |
| ProspectGroupMember | UUID; validated group/person relation | both related entities belong to same school | CRM |
| EnrollmentInterest | UUID; explicit grade/entry year | links to school-scoped group; optional verified canonical application ID | CRM |
| VerifiedIdentityLink | UUID; source and target object typed; approved evidence | same school, uniqueness of active exact link, review and revoke | CRM references, Core source truth |
| CRMTask | UUID; separate idempotency key for generated work | school, assignee authorized at mutation time | CRM |
| CRMConsentEvent | UUID append-only provenance | purpose, channel, subject, recorded source and time | CRM consent decisions, comms sends |
| RelationshipTimelineRow | read-only projection identifier | scoped per school, filtered per caller rights | Aggregated origin records |

Do not require a child name, DOB, health data or protected school records merely to capture a grade-interest opportunity.

## 5. Proposed use cases (acceptance journeys)

1. Anonymous adult submits public inquiry twice with identical request key -> one inquiry, one persistent retry receipt.
2. Same email contacts same school twice with different request keys -> two distinct inquiry records and restricted candidate suggestions; no public information leakage.
3. Same contact details submitted for another school -> separate tenant records; no cross-school match or query.
4. One family has two children, two applications and one confirmed enrollment -> family report counts one captured family, two applications, one or more canonical confirmed applications without stage regression.
5. Counselor assignment changed mid-queue -> task owner and audit reflect authorized actor; notifications revalidate ownership.
6. An inquiry requests a tour -> request captured, not falsely represented as booked appointment.
7. A family withdraws optional follow-up consent while an outbox message is queued -> dispatch guard suppresses unauthorized send and records outcome.
8. Existing guardian's email matches an inquiry -> CRM proposes an identity-link candidate only to authorized staff; never grants portal access or merges identities automatically.
9. Marketing viewer opens 360 profile -> no finance, sensitive student, donor, pastoral or admissions decision data without separate permission.
10. Staff creates/completes an overdue follow-up task -> task state records completion; a queued email alone cannot complete it.
11. Campaign report measures family inquiries against family conversions and separately measures child applications; actual revenue remains absent without verified ledger linkage.
12. A migration fails halfway on a synthetic 2-school PostgreSQL copy -> rolled back or resumed idempotently; row counts and relationship mappings reconciled.
13. Outbox retries and event replays are reordered -> no double notifications or duplicate tasks.
14. School-aware list/report export of a foreign-school ID -> fail closed with no disclosure.

## 6. Controlled implementation backlog

No work below is authorized as completed by the presence of this document. The execution order is small and dependency driven.

| Slice | Change boundary | Tests/evidence | Dependency and reversal |
| --- | --- | --- | --- |
| CR-00 | Approve ADR-0006; reconcile approved owner matrix and API contract | Accepted ADR entry and diff inspection | No data writes; doc revert only |
| CR-01 | Independent close-out of existing PR #353 sibling regression | Same-source focused tests, tenant negatives, protected checks | Must land separately; revert service/tests if needed |
| CR-02 | Prospective group/contact/interest additive schema only | PostgreSQL migration drill, same-school FKs, distinct children, old API compatibility, rollback | ADR and lifecycle acceptance; no destructive migration |
| CR-03 | Verified identity-link workflow (no auto-merge) | Unauthorized, mixed school, duplicate, revoked, simultaneous link tests and audit | CR-02; reversible link status |
| CR-04 | CRMTask schema and transaction services | Due/assigned/completed, role changes, exactly-once creation and concurrent transitions | CR-02; no provider dispatch |
| CR-05 | CRM queue/timeline read API + pagination | Query count/EXPLAIN, stable ordering, tenant/rbac, compatibility | CR-04; old inquiry endpoints preserved |
| CR-06 | Relationship Center React views | Accessibility, real transport/empty/error/loading states, E2E same-school restrictions | CR-05; feature flag rollback |
| CR-07 | Consent ledger and controlled comms extension | Per-channel/purpose grant/withdrawal, old default-off, suppression and retry | Governance approval; no default activation |
| CR-08 | Campaign/event attribution and read-only advancement adapters | Unit/reconciliation metrics, permissions, source lineage | CR-06; rollback projection only |
| CR-09 | Staging/post-deploy operational acceptance | Exact SHA, migration version, worker, browser, provider only when separately authorized, restore | Never infer deployed readiness from merge |

Keep code, schema, security permission, UI, and live external activation changes in distinct PRs unless tightly inseparable and independently testable.

## 7. Phase 0 exit gate

All must be true before CR-02 migration proposal proceeds:

- [ ] Proposed ADR-0006 reviewed/accepted and indexed through governance.
- [ ] Exact accepted-head tests and open overlapping PRs reconciled; #353 has a documented final disposition.
- [ ] Canonical identity writer and CRM read-only/verified-link boundaries accepted.
- [ ] Opportunity stage aggregation policy accepted, including siblings and multi-year cases.
- [ ] CRM prospective contact group and relationship-link semantics approved with custody/portal restriction test plan.
- [ ] Separate inquiry-response, marketing and channel consent purposes/retention decision approved.
- [ ] CRM permission matrix and 360 field classification approved.
- [ ] Existing model/API consumers and migrations inventoried; no duplicate writers.
- [ ] PostgreSQL expansion/recovery and representative synthetic tenant reconciliation designed.
- [ ] Small-slice acceptance criteria and rollback steps assigned.

## 8. Repository verification and claim limits

The inspected accepted-main baseline is 433aa0b6cb54c3b5a86f50f5f3137c46ebb12940. Draft #353 was open at inspection with two changed files and no locally executed tests reported in its PR. This document records source-observed gaps and proposed decisions only. It does not imply any model was migrated, route released, permission granted, worker enabled, real family contacted, deployment changed, or infrastructure cost incurred.

Reference release-governance source: [CURRENT_RELEASE_STATUS](../CURRENT_RELEASE_STATUS.md); [accepted architecture index](../architecture/DECISION_INDEX.md). 
