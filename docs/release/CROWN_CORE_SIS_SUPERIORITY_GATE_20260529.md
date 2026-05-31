# CROWN Core SIS Superiority Gate — 2026-05-29

## Decision

**SUPERIORITY CERTIFICATION: NO-GO**

CROWN must not be represented as superior to the private-school SIS market until every gate in this file is green with current evidence from the reviewed branch/commit.

This is not a product-positioning document. It is the proof standard for certifying that the CROWN core SIS is strong, healthy, clean, and objectively superior to the 25-product private-school competitor set.

## Current verified posture

The current repository evidence supports this status:

- CROWN is a release-candidate / sandbox-hardening codebase, not GA.
- CROWN is not pilot-approved.
- P0 and governance evidence lanes are materially mature.
- Release authority remains on integrity hold.
- The full-completion branch adds a truth gate and blocker file, but PR #866 is draft/open and not merged.
- The current full-completion blocker file marks full module/dashboard/component/wizard certification as NO-GO.
- The frontend dashboard registry covers broad Tier 1, Tier 2, later-tier, mission, and platform dashboards.
- The backend has broad installed-app/domain coverage and a 29-entry wizard registry.
- Registry and route coverage are not the same as completion.
- Dashboard templates and backend dashboard payload paths still contain sample/preview/fallback signals that block certification.
- Current CI/workflow evidence was not returned by the connector for the inspected head.
- Compliance/customer-readiness, pilot proof, and founder acceptance remain release blockers.

## Certification rule

A CROWN capability is **COMPLETE** only when all required evidence exists for the exact reviewed commit:

1. Route exists.
2. Runtime page/API renders.
3. Backend model/service/API exists where applicable.
4. Dashboard data is live or explicitly certified for the deployment context.
5. No sample/template/fallback data is hidden behind a ready status.
6. Permissions/RBAC are enforced.
7. Tenant isolation is proven.
8. Wizard/workflow completes end-to-end where applicable.
9. Frontend tests pass.
10. Backend tests pass.
11. Accessibility proof exists.
12. Responsive proof exists.
13. Screenshots, logs, or CI artifacts exist.
14. Evidence files are current to the reviewed commit.
15. Compliance/customer-readiness artifact exists where the workflow touches student, family, staff, financial, health, or communications data.

Any missing item makes the capability **NOT CERTIFIED**.

## Superiority gates

| Gate | Name | Required result | Current status | Blocking reason |
|---|---|---:|---|---|
| S0 | Release authority and language control | Public/product claims match repo evidence | BLOCKED | Repo still says no GA, no pilot approval, integrity hold |
| S1 | Core SIS data model | Student, household, enrollment, attendance, course, section, grade, transcript, staff, financial, communication, and tenant records proven | IN_PROGRESS | Broad app/domain coverage exists; commit-current proof register still required |
| S2 | Live dashboard truth | Every dashboard widget has live service/API provenance or certified sandbox flag | BLOCKED | Template BASE_NOTE and sample/fallback payload signals remain |
| S3 | Runtime workflow proof | Every core school workflow completes in browser/API proof | BLOCKED | Registry coverage exists; end-to-end workflow proof still required |
| S4 | Wizard completion | All 29 backend-registered wizards complete end-to-end | BLOCKED | Registry exists; PR blocker tracks wizard proof as not certified |
| S5 | Security and tenant isolation | Tenant isolation, RBAC, route permissions, object authorization, and secret scans green | IN_PROGRESS | P0/governance lanes mature; current gate evidence still required |
| S6 | Compliance/customer readiness | FERPA, COPPA, DPA, retention, support access, incident response, subprocessors, backup/restore, sandbox/no-real-data, pilot criteria complete | BLOCKED | Compliance/customer-readiness packet is open |
| S7 | UX and accessibility | Accessible, responsive, low-friction, role-specific workflows proven by tests/screenshots | IN_PROGRESS | Frontend scripts exist; current execution artifacts required |
| S8 | Competitor superiority | CROWN equals or exceeds each competitor in critical private-school lanes with evidence | NOT_CERTIFIED | Competitor matrix exists in this gate; CROWN evidence does not yet close all lanes |
| S9 | Operational release proof | Backend, frontend, dependency, secret, migration, health, deploy, KPI source, accessibility, responsive, evidence bundle all green | BLOCKED | Current full-completion gate requires execution and artifact attachment |

## 25-competitor benchmark set

| # | Competitor | Market role | What CROWN must beat | Current CROWN result |
|---:|---|---|---|---|
| 1 | Veracross | Private/independent K-12 SIS with one-person/one-record positioning, broad departments, integrations | Match single-record integrity, departmental breadth, integration maturity; exceed with Christian-school workflows, proof gates, cleaner data provenance | NOT_CERTIFIED |
| 2 | FACTS / RenWeb | Large private/Christian/Catholic K-12 platform covering academics, finance, family engagement, analytics | Match admissions/academics/finance/family coverage and trust; exceed with cleaner UX, live operational dashboards, tenant proof | NOT_CERTIFIED |
| 3 | Blackbaud Education Management | K-12 suite spanning SIS, LMS, enrollment, billing, advancement/nonprofit ecosystem | Match SIS/enrollment/billing/LMS/advancement breadth; exceed with simpler school operations and Christian-specific workflows | NOT_CERTIFIED |
| 4 | PowerSchool | Large K-12 operations/SIS incumbent | Match core SIS depth, reporting, scale, and integrations; exceed on private-school fit, security posture, transparency, and implementation cleanliness | NOT_CERTIFIED |
| 5 | Alma | Modern SIS with analytics, integrations, attendance, grading, records, scheduling, communications | Match modern SIS usability and analytics; exceed on full Christian school operating model and evidence-gated release discipline | NOT_CERTIFIED |
| 6 | Finalsite Enrollment / SchoolAdmin | Enrollment, admissions, communications, marketing, websites | Beat specialized enrollment/marketing while tying enrollment into live SIS, billing, records, and dashboards | NOT_CERTIFIED |
| 7 | Ravenna | Private-school admissions/application/progress management | Match application/event/progress workflows; exceed by converting admissions into full SIS, billing, family, and registrar records | NOT_CERTIFIED |
| 8 | TADS / VenturEd | Private/independent contracts, billing, tuition, SIS, admissions, financial aid | Match lifecycle enrollment/billing support and retention-quality service; exceed with unified live operations and stronger dashboards | NOT_CERTIFIED |
| 9 | Rediker | Full school administrative SIS with gradebook, admissions, billing, portals, master schedule | Match SIS/admin breadth; exceed with modern architecture, Christian mission layer, and objective evidence gates | NOT_CERTIFIED |
| 10 | Senior Systems | Independent-school integrated database across admissions, academics, accounting, advancement | Match single-database independent-school operating depth; exceed with current UI, proof automation, and broader module truth register | NOT_CERTIFIED |
| 11 | Skyward | District/K-12 student management, HR, finance, ERP-style incumbent | Match student management + ERP reliability; exceed on private Christian market specificity and evidence transparency | NOT_CERTIFIED |
| 12 | Infinite Campus | Large district SIS incumbent | Match SIS scale, scheduling, grading, reporting, family portal, security; exceed on private-school fit and proof-backed release discipline | NOT_CERTIFIED |
| 13 | Gradelink | Private-school-friendly SIS with gradebook, attendance, enrollment, support | Match simplicity/support; exceed on full operating system breadth and live dashboards | NOT_CERTIFIED |
| 14 | QuickSchools | Cloud SIS with gradebook, attendance, admissions, scheduling, fees, messaging, reports | Match lightweight SIS speed; exceed on enterprise-grade tenant, compliance, and Christian workflows | NOT_CERTIFIED |
| 15 | MySchoolWorx | Small/private-school management competitor | Match gradebook/attendance/family operations; exceed on completeness, dashboards, security, compliance, and implementation proof | NOT_CERTIFIED |
| 16 | Sycamore | Small/mid private K-12 all-in-one with SIS, payments, LMS, communications, scheduler | Match all-in-one private-school operations; exceed on proof gates, tenant posture, and deeper dashboards | NOT_CERTIFIED |
| 17 | SchoolCues | Small-school admin, SIS, payments, admissions/enrollment, alumni, parent engagement | Match small-school ease; exceed on full SIS + finance + mission + governance depth | NOT_CERTIFIED |
| 18 | SchoolSpeak | K-12/Catholic/private integrated school management with gradebook, attendance, payments, communications | Match Catholic/private workflows; exceed on modern architecture, dashboards, tenant safety, and full module breadth | NOT_CERTIFIED |
| 19 | openSIS | Cloud SIS with student, staff, attendance, grades, behavior, fees, RBAC, compliance positioning | Match core SIS and affordability; exceed on private Christian workflows and operational dashboards | NOT_CERTIFIED |
| 20 | DreamClass | School management for admissions, academics, students, teachers, scheduling, finance, access, communications | Match paperless workflows and tuition/academic basics; exceed on breadth and evidence discipline | NOT_CERTIFIED |
| 21 | Classe365 | All-in-one CRM/SIS/LMS/finance/fundraising/alumni platform | Match full learner lifecycle; exceed with Christian/private specificity | NOT_CERTIFIED |
| 22 | Fedena | Global school ERP with 100+ modules and broad adoption | Match breadth and ERP depth; exceed on U.S. private Christian compliance, UX, and proof discipline | NOT_CERTIFIED |
| 23 | Edsembli / Sparkrock | K-12 finance, HR, SIS, school-generated funds platform | Match finance/HR/SIS integration; exceed on private-school mission fit and all-module dashboards | NOT_CERTIFIED |
| 24 | SchoolMint | Enrollment/recruitment/application/lottery/registration/analytics and behavior/data tools | Match enrollment excellence; exceed by connecting enrollment to full SIS, billing, registrar, and parent/student operations | NOT_CERTIFIED |
| 25 | FACTS Financial / Tuition ecosystem | Tuition, billing, payments, financial aid operating lane | Match trust and finance workflows; exceed by making finance native to the SIS operating record and dashboards | NOT_CERTIFIED |

## CROWN superiority thesis

CROWN can become objectively stronger than this market only by winning five lanes simultaneously:

1. **Integrity lane:** tenant isolation, RBAC, route authorization, object-level authorization, secret hygiene, and no real data in sandbox.
2. **Truth lane:** no dashboard, KPI, workflow, or release claim uses hidden sample/template/fallback data.
3. **Workflow lane:** every school job has a complete operational path, not just a page, route, or registry entry.
4. **Mission lane:** spiritual life, service hours, chapel/community signals, Christian-school governance, family engagement, and stewardship workflows are first-class, not bolt-ons.
5. **Implementation lane:** setup, import, migration, sandbox proof, training, support access, rollback, backup/restore, and pilot entry/exit are controlled and evidence-backed.

## Current strongest CROWN advantages

| Advantage | Evidence-backed? | Why it matters |
|---|---|---|
| Evidence-first release discipline | YES | The repo prevents unsupported GA/pilot claims and tracks blockers explicitly |
| Broad dashboard registry | YES | CROWN has declared a wider school operating surface than many SIS-only products |
| Broad backend domain surface | PARTIAL | Backend app/domain coverage exists, but per-module runtime proof is still required |
| Wizard architecture | YES for registry, NOT_CERTIFIED for end-to-end completion | The backend has a single-source wizard registry with 29 entries |
| Security posture | PARTIAL | Sensitive-data and tenant-isolation severity rules exist; current full proof still required |
| Christian-school differentiation | PARTIAL | Mission/spiritual-life surfaces exist, but full workflow/runtime proof is required |

## Current hard blockers

| Blocker | Certification impact | Required closure |
|---|---|---|
| Dashboard preview/fallback data | Blocks superiority and completion | Replace template metrics with live service/API-backed data or explicit sandbox-only certification |
| Backend sample/fallback payload builders | Blocks production-grade dashboard certification | Production/full-completion mode must refuse sample payload certification |
| Missing current CI/workflow proof | Blocks all test-pass claims | Run and attach current gate outputs for the reviewed branch |
| Registry coverage treated as completion | Blocks honest scorekeeping | Maintain module-by-module proof matrix and mark incomplete lanes as NOT_CERTIFIED |
| Later-tier backend/runtime gaps | Blocks all-module completion | Add API, service, permission, and Playwright proof for later-tier modules |
| Compliance/customer-readiness open | Blocks pilot, GA, and market superiority | Complete FERPA, COPPA, DPA, retention, support access, incident response, subprocessors, backup/restore, sandbox/no-real-data, pilot criteria |
| Founder acceptance not signed | Blocks final authority | Obtain explicit final acceptance after evidence gates are green |

## Required repo evidence package

After remediation and execution, the certifying packet must include these current artifacts:

```text
.crown-audit/full-completion-truth/latest/00_SUMMARY.md
.crown-audit/full-completion-truth/latest/10_dashboard_template_preview_blockers.csv
.crown-audit/full-completion-truth/latest/20_backend_sample_payload_blockers.csv
.crown-audit/full-completion-truth/latest/30_required_scope_status.csv
.crown-audit/full-completion-truth/latest/99_STATUS.json
.crown-audit/dashboard-completion/latest/00_SUMMARY.md
.crown-audit/dashboard-completion/latest/30_check_results.csv
.crown-audit/dashboard-completion/latest/40_module_dashboard_matrix.csv
.crown-audit/dashboard-completion/latest/50_blockers.md
.crown-audit/dashboard-completion/latest/99_STATUS.json
docs/release/CROWN_CORE_SIS_MODULE_PROOF_REGISTER_20260529.csv
docs/release/CROWN_CORE_SIS_COMPETITOR_MATRIX_20260529.csv
docs/release/CROWN_CORE_SIS_REMEDIATION_LEDGER_20260529.csv
```

## Final certification sentence

The only acceptable final claim after all gates are green is:

> CROWN has been certified against the 2026 private-school SIS superiority gate, with current evidence proving complete core SIS workflows, live operational dashboards, tenant-safe architecture, compliance/customer readiness, and equal-or-better coverage against the 25-product competitor set.

Until then, the correct claim is:

> CROWN has strong architectural direction and evidence discipline, but superiority certification remains NO-GO until all gates close with current proof.
