# CROWN Final 95+ Acceptance Matrix - 2026-05-30

Status: FINAL-SPRINT CONTROL MATRIX
Authority: Non-shipping control document until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Standard

Every surfaced module, workflow, route, dashboard, API, permission path, and data flow must score 95+ or remain `NOT DONE` for production release.

Scoring is evidence-first. A present file, route, registry row, or dashboard shell is not completion. Completion requires backend, frontend, workflow, tenant/RBAC, live/proven data, error states, tests, and release evidence.

## Score columns

| Column | Meaning |
|---|---|
| Backend/API | Models, services, URLs, serializers/schema, validation |
| Frontend/UX | Route, page, role journey, responsive/accessible UX |
| Workflow | End-to-end process complete for real user role |
| Data | Live/proven source or honest state label with provenance |
| Security | Tenant, RBAC, object permission, audit/idempotency where needed |
| Tests | Local/CI proof, negative tests, contract tests |
| Evidence | Committed artifact or command output |
| Status | PASS, NOT DONE, or NOT VERIFIED |

## Release-wide gates

| Gate | Required final state | Current connector-backed status | Next proof required |
|---|---|---|---|
| Canonical release authority | Current SHA, current evidence, no contradictions | NOT DONE - current authority still says CONDITIONAL GO and blocks unrestricted GA | Refresh only after proof run |
| Deploy SHA parity | PASS on current candidate and target | NOT DONE - canonical authority still says PARTIAL / NOT YET CLOSED | Run parity script and commit artifacts |
| Protected spine | PASS on exact candidate SHA | NOT DONE - canonical authority still says PARTIAL | Run full protected-spine packet |
| Frontend build/contracts | PASS current candidate | NOT VERIFIED for latest connector commits | Run VS Code command pack |
| Backend check/migrations | PASS current candidate | NOT VERIFIED for latest connector commits | Run VS Code command pack |
| Tenant/RBAC | PASS current candidate | NOT VERIFIED for latest connector commits | Run VS Code command pack |
| Module acceptance | 95+ all in-scope rows | NOT DONE | Complete rows below with proof |

## Module matrix

| Module / Surface | Backend/API | Frontend/UX | Workflow | Data | Security | Tests | Evidence | Status | Required final-sprint action |
|---|---|---|---|---|---|---|---|---|---|
| Identity / RBAC / Tenant Enforcement | PRESENT | PRESENT | NOT VERIFIED | PARTIAL | PARTIAL | PARTIAL | Tenant tests exist historically | NOT DONE | Expand role/object/tenant proof across every sensitive module and reconcile backend/frontend role vocabulary |
| Core SIS Student Records | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Core models inspected | NOT DONE | Prove student/family/guardian/household CRUD/read flows, permissions, audit, exports |
| Admissions Pipeline | PRESENT | PRESENT | PARTIAL | PARTIAL | PARTIAL | PARTIAL | Admissions routes/hooks/dashboard inspected; PR #883 adds operational wiring | NOT DONE | Run endpoint tests, route tests, data provenance proof, accepted-to-enrolled proof |
| Enrollment / Re-enrollment | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Admissions lifecycle code inspected | NOT DONE | Prove accepted-to-enrolled, contract, deposit, classroom readiness, portal activation |
| Billing / Tuition Obligations | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | PARTIAL | Billing routes and finance handoff present | NOT DONE | Prove plans, invoices, statements, parent view, finance view, tenant/RBAC, tests |
| Payments / Ledger | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Ledger immutability pattern inspected | NOT DONE | Prove provider handoff, reconciliation, reversals, audit, exceptions, statements |
| Financial Aid | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Registry/routes present | NOT DONE | Prove application, review, award, budget, contract/billing sync |
| Attendance | PRESENT | PRESENT | NOT VERIFIED | PARTIAL | NOT VERIFIED | NOT VERIFIED | Registry/routes present | NOT DONE | Prove teacher submit, parent view, admin exceptions, reports, KPI source |
| Gradebook | PRESENT | PRESENT | NOT VERIFIED | PARTIAL | NOT VERIFIED | PARTIAL | Frontend proof scripts exist | NOT DONE | Prove grade entry, weights, parent/student views, report readiness, API/UI tests |
| Scheduling | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Registry/routes present | NOT DONE | Prove terms, sections, student schedule, teacher/parent routes, calendar assignments |
| Communications / CRM | PRESENT | PRESENT | NOT VERIFIED | PARTIAL | NOT VERIFIED | NOT VERIFIED | Admissions CRM hook and comms routes inspected | NOT DONE | Prove messages, campaigns, delivery failures, parent/staff comms, CRM lifecycle |
| LMS / Online Classroom / Learning Continuity | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Learning-continuity routes present | NOT DONE | Prove Teams/MS365 classroom path, teacher daily cockpit, student today, parent learning status |
| Curriculum / Lesson Plans / Scope Sequence | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Curriculum import route present | NOT DONE | Prove BJU/Abeka/Purposeful Design import/edit/map-to-calendar workflow |
| Student Care / Counseling / Discipline | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Routes/apps present | NOT DONE | Prove incident/care/intervention workflows and permissions |
| Health Office | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Registry/routes present | NOT DONE | Prove immunizations, visits, meds, alerts, reports |
| Transportation | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Registry/routes present | NOT DONE | Prove routes, riders, exceptions, parent visibility |
| Food Service | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Registry/routes present | NOT DONE | Prove meal operations, eligibility, orders, reports |
| HR | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Registry/routes present | NOT DONE | Prove staff records, onboarding, credentials/compliance, permissions |
| Facilities | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Registry/routes present | NOT DONE | Prove work orders, assets, maintenance, requests |
| Safety / Security | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Registry/routes present | NOT DONE | Prove incidents, drills, access, emergency workflows |
| Fine Arts | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Registry/routes present | NOT DONE | Prove rosters, events, communications, reporting |
| Library / Media | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Registry/routes present | NOT DONE | Prove catalog, circulation, media resources, student/teacher access |
| Extended Care / Aftercare | PRESENT | PRESENT | PARTIAL | NOT VERIFIED | NOT VERIFIED | PARTIAL | Aftercare proof slice referenced by authority | NOT DONE | Re-run aftercare proof on current candidate and prove billing/attendance/parent visibility |
| Summer Camp | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Registry/routes present | NOT DONE | Prove setup, registration, roster, billing, attendance |
| Spiritual Life / Service Hours | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Registry/routes present | NOT DONE | Prove chapel, service, discipleship workflows and reporting |
| Advancement / Alumni | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Registry/routes present | NOT DONE | Prove donor/campaign/alumni operations, payments, reports |
| Board / Governance | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Board routes/apps present | NOT DONE | Prove packets, governance dashboard, initiatives, risk/compliance metrics |
| Platform Operations | PRESENT | PRESENT | NOT VERIFIED | PARTIAL | NOT VERIFIED | PARTIAL | PR #882 restored several later-tier metrics | NOT DONE | Prove tenant health, implementation, data migration, integrations, compliance, release reliability |
| Compliance / Customer Readiness | PRESENT | PRESENT | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Historical limitations list required proof set | NOT DONE | Publish FERPA, COPPA, DPA, retention, support access, incident, subprocessors, backup/restore, sandbox policy |
| Release / CI / Deploy | PRESENT | PRESENT | PARTIAL | PARTIAL | PARTIAL | PARTIAL | Workflows inspected | NOT DONE | Run full current candidate proof, parity, protected spine, policy gates |

## Global blockers to 95+

1. Current canonical authority still blocks unrestricted GA.
2. Current scorecard still has scores below 95.
3. Many modules have presence but not full proof.
4. Dashboard registry defaults to `draft`; presence does not equal live completion.
5. API routing includes compatibility/legacy catch-all behavior that must be audited.
6. Frontend router contains direct routes outside the generated dashboard registry that require guard classification.
7. Role vocabulary must be reconciled across backend, frontend, nav, permissions, and tests.
8. Runtime evidence must be generated locally or through CI for the latest candidate SHA.

## Completion rule

Do not promote a row to PASS unless the corresponding evidence artifact exists and the score is 95+.
