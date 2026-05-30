# CROWN Guided Proof Sandbox Blueprint

Status: Implementation baseline
Owner: CROWN Product
Last updated: 2026-05-28

## Decision

CROWN will use a Guided Proof Sandbox instead of a raw sandbox-only experience.

The sandbox must support three vertical demo tracks:

1. School Demo
2. Daycare / Early Learning Demo
3. Camp / Summer Program Demo

Each track must support two evaluator modes:

1. Guided path
2. Self-guided exploration

Guided path is the default for first-time evaluators. Self-guided exploration is available after the user understands the demo-data boundary and basic product story.

## Why this approach

A raw sandbox creates cognitive load. A buyer has to figure out what to click, which role matters, which data is meaningful, and whether incomplete-looking areas are defects or simply not part of the demo story.

A guided proof sandbox reduces that load by giving the evaluator:

- The right vertical context
- The right school, daycare, or camp archetype
- The right persona
- A short proof path
- Safe demo data
- Optional freedom to explore independently

## UX model

### Entry point

Primary route: `/sandbox`

The landing page must answer:

1. What kind of organization am I evaluating for?
2. Do I want guided or self-guided exploration?
3. Which role do I want to enter as?
4. What fictional scenario will I see?

### Track selection

| Track | Target evaluator | Core value story |
| --- | --- | --- |
| School Demo | K-12 Christian school, academy, hybrid school | One connected operating system from leadership to classroom to family |
| Daycare / Early Learning Demo | Preschool, daycare, church early learning center, PK program | Parent trust, check-in/out, billing, staff workflow, daily communication |
| Camp / Summer Program Demo | Summer camp, VBS-style program, enrichment week, school-run seasonal program | Registration, rosters, payments, attendance, safety notes, family updates |

### Mode selection

| Mode | Default user | Experience |
| --- | --- | --- |
| Guided path | First-time external evaluator | CROWN gives the user a checklist and next-best action sequence |
| Self-guided exploration | Qualified evaluator after intro; internal QA; pilot rehearsal | User can explore modules freely with visible role/school context and demo-data warnings |

## Required vertical demo stories

### School Demo

Primary story: Run a Christian school day.

Required proof path:

1. Head of School opens operating dashboard.
2. Admissions Director reviews inquiry-to-enrollment workflow.
3. Teacher takes attendance or reviews class context.
4. Parent reviews student and family account context.
5. Finance Director reviews balances or receivables risk.

Required personas:

- Head of School / School Admin
- Admissions Director
- Finance Director
- Teacher
- Parent
- Student

### Daycare / Early Learning Demo

Primary story: Build parent trust and make daily care operations efficient.

Required proof path:

1. Director reviews daily attendance and classroom status.
2. Staff checks a child in or out.
3. Staff reviews allergy or care-note placeholder.
4. Parent receives or views daily update.
5. Finance reviews family balance or recurring care charge.

Required personas:

- Director / School Admin
- Staff / Teacher
- Parent / Guardian
- Finance Director
- Admissions Director for enrollment pipeline, if applicable

Student/camper self-service is not required for daycare unless a specific customer segment needs it.

### Camp / Summer Program Demo

Primary story: Manage seasonal program registration through daily roster operations.

Required proof path:

1. Program Director reviews session enrollment and capacity.
2. Admissions/Registration Director reviews registrations by status.
3. Staff checks campers into a session or group.
4. Parent reviews schedule, payment, and update context.
5. Finance reviews camp fees, unpaid balances, and payment follow-up.

Required personas:

- Program Director / School Admin
- Admissions or Registration Director
- Finance Director
- Staff / Teacher
- Parent / Guardian
- Student / Camper, when age-appropriate

## Guided path behavior

Guided path must include a command center or checklist visible after login.

Minimum checklist fields:

- Current track
- Current archetype
- Current role
- Current scenario
- Step count
- Next action
- Switch role
- Switch archetype
- Reset scenario
- Submit feedback

Example:

```text
Track: Camp / Summer Program Demo
Scenario: Session Registration to Daily Roster
Role: Program Director
Step 1 of 5: Review session capacity and roster health.
```

## Self-guided behavior

Self-guided mode must not be a blank product dump. It must still include:

- Demo-data badge
- Role context
- Track context
- Switch role
- Switch scenario
- Reset scenario
- Optional checklist collapsed by default
- Feedback link

Self-guided mode gives freedom after orientation; it does not remove safety controls.

## Seed pack model

Each track needs deterministic seed packs.

Recommended structure:

```text
sandbox/seed_packs/
  school/heritage_core/
    manifest.json
    users.json
    families.json
    students.json
    admissions.json
    attendance.json
    gradebook.json
    finance.json
    communications.json
    expected_metrics.json

  daycare/emmanuel_early_learning/
    manifest.json
    users.json
    children.json
    families.json
    care_rooms.json
    checkin_checkout.json
    billing.json
    communications.json
    safety_notes.json
    expected_metrics.json

  camp/cedar_ridge_summer_camp/
    manifest.json
    users.json
    campers.json
    families.json
    sessions.json
    registrations.json
    rosters.json
    payments.json
    communications.json
    safety_notes.json
    expected_metrics.json
```

## Reset model

Every seed pack must support:

- Full reset
- Scenario reset
- Idempotent re-seed
- Expected metric verification
- Role permission verification

Required commands:

```bash
python manage.py sandbox_seed --track school --pack heritage_core --reset
python manage.py sandbox_seed --track daycare --pack emmanuel_early_learning --reset
python manage.py sandbox_seed --track camp --pack cedar_ridge_summer_camp --reset
python manage.py sandbox_verify --track school --pack heritage_core
```

## Route and UI implementation baseline

Implemented baseline files:

- `frontend/dashboards/src/sandbox/sandboxExperience.js`
- `frontend/dashboards/src/pages/SandboxLandingPage.jsx`
- `docs/compliance/SANDBOX_DATA_POLICY.md`

Router integration requirement:

- Import `SandboxLandingPage` in `frontend/dashboards/src/routes/router.jsx`
- Add route `{ path: '/sandbox', element: <SandboxLandingPage /> }`

Login integration requirement:

- Login page must read query params:
  - `mode=sandbox`
  - `experience=school|daycare|camp`
  - `guidance=guided|self-guided`
  - `role=<persona>`
  - `school=<school_id>`
  - `tour=<tour title>`
- In sandbox mode, selected persona and school must preselect automatically.
- Visible credential handling should be minimized; role cards should be primary.

## Release gates

A buyer-facing sandbox is not ready until all gates pass:

| Gate | Requirement |
| --- | --- |
| UX route | `/sandbox` renders without build error |
| Track selection | School, daycare, and camp tracks visible |
| Mode selection | Guided and self-guided modes visible |
| Persona start | Each visible persona produces a valid login URL |
| Login context | Login preselects role and school from URL params |
| Demo data label | Landing and login both display demo-data warning |
| Seed pack | At least one deterministic seed pack exists per track |
| Reset | Each seed pack can reset and verify expected metrics |
| Role proof | Persona permissions are verified |
| Cross-tenant proof | User cannot access another sandbox tenant context |
| Feedback | Evaluator can submit feedback from sandbox |
| Compliance | Sandbox data policy active and followed |

## Product rule

The sandbox is not just a place to click features. It is a proof path that shows how CROWN operates a school, daycare, or camp with safe fictional data.
