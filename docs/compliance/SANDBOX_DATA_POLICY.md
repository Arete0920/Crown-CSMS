# Sandbox Data Policy

Status: Active for sandbox and controlled-demo work
Owner: CROWN Product / Compliance
Last updated: 2026-05-28

## Purpose

This policy defines the required data-handling controls for every CROWN sandbox, demo, guided proof environment, self-guided evaluation environment, internal QA environment, and controlled pilot rehearsal environment.

The sandbox exists to let evaluators understand CROWN workflows without exposing real student, child, camper, family, staff, financial, health, safety, disciplinary, or institutional records.

## Scope

This policy applies to:

- School demo tracks
- Daycare / early learning demo tracks
- Camp / summer program demo tracks
- Sales-led guided demonstrations
- Self-guided evaluator sandboxes
- Internal QA sandboxes
- Seed packs, reset scripts, screenshots, exported proof artifacts, and demo manifests

## Required rule

Sandbox data must be fictional, clearly labeled, resettable, and tenant-scoped.

No real records may be entered, imported, pasted, uploaded, synced, exported into, or manually recreated inside a sandbox environment.

## Prohibited data

The following data is prohibited in sandbox environments:

- Real student, child, camper, applicant, or alumnus data
- Real family, parent, guardian, emergency contact, or household data
- Real staff, volunteer, teacher, coach, or counselor data
- Real tuition, payment, scholarship, donor, payroll, or financial data
- Real health, allergy, medication, counseling, discipline, safety, incident, or attendance data
- Production database dumps
- Production environment variables
- Production API keys, bearer tokens, refresh tokens, client secrets, certificates, or private keys
- Microsoft 365 tenant secrets or production OAuth credentials
- Screenshots or exports containing real school records

## Permitted data

The following data is permitted when clearly labeled as sandbox/demo data:

- Fictional schools, daycares, camps, classes, groups, sessions, terms, programs, and divisions
- Fictional students, children, campers, applicants, families, staff, volunteers, and users
- Fictional balances, invoices, payments, discounts, scholarships, and receivables
- Fictional attendance, grade, application, enrollment, communication, and support records
- Fictional safety notes that cannot be confused with real incidents
- Deterministic seed data used for repeatable dashboard metrics and test assertions

## Labeling controls

Every sandbox experience must include visible demo-data labeling at these locations:

1. Public sandbox landing page
2. Login page
3. Authenticated dashboard shell or command center
4. Form pages that accept free text
5. Export, screenshot, and evidence bundles
6. Feedback forms and pilot intake forms

Minimum required label text:

> Demo data only. Do not enter real student, child, camper, family, staff, financial, health, safety, or disciplinary records.

## Track-specific controls

### School demo

The school demo must show K-12 workflows using fictional school records only. It may include admissions, attendance, academics, finance, communications, family access, student access, transportation, athletics, and operations workflows.

### Daycare / early learning demo

The daycare demo must show fictional child-care workflows only. It may include check-in/out, classroom groups, caregiver communication, billing, allergy flags, staff notes, incident-style examples, and family updates. Any health or safety example must be visibly fictional and non-sensitive.

### Camp / summer program demo

The camp demo must show fictional seasonal-program workflows only. It may include registration, session rosters, attendance, payment status, activity groups, pickup authorization, medical-note placeholders, and family updates. Medical-note examples must be generic and fictional.

## Guided vs self-guided use

CROWN supports two demo modes:

| Mode | Intended use | Data control requirement |
| --- | --- | --- |
| Guided path | First-time evaluator, live demo, sales-led walkthrough, controlled proof | Guided checklist, role context, demo-data badge, no real-data warning |
| Self-guided exploration | Qualified evaluator after intro, internal QA, pilot rehearsal | Same controls plus reset/revoke path and clear sandbox boundary |

Guided mode is the default for first-time external evaluators. Self-guided mode is acceptable only when the evaluator has already seen the sandbox boundary and demo-data warning.

## Seed and reset controls

Every seed pack must be:

- Deterministic
- Tenant-scoped
- Idempotent or safely resettable
- Bound to a named demo track and archetype
- Backed by expected metric assertions where dashboards display KPIs
- Reproducible through a documented management command or reset workflow

Every sandbox must have a reset path before broad evaluator access.

## Access controls

Sandbox access must be role-scoped. Each evaluator should enter through one of the approved personas:

- Head of School / School Admin
- Admissions Director
- Finance Director
- Teacher / Staff
- Parent / Guardian
- Student / Camper, when appropriate

Invite-token or gated access should be used for controlled external self-guided evaluation.

## Export controls

Sandbox exports, screenshots, and evidence bundles must be watermarked or labeled as demo/sandbox output. Exported files must not be used as production templates unless the content has been reviewed and scrubbed.

## Verification controls

Before sandbox expansion, verify:

- Login works for every visible persona
- School, daycare, and camp tracks render the correct scenario cards
- Role routes land in the correct dashboard or approved fallback route
- Demo-data warnings appear on landing and login surfaces
- No seeded record uses real names, real domains, real phone numbers, real addresses, or real payment identifiers
- Reset process restores expected metrics
- Cross-tenant access is blocked

## Incident handling

If real data is discovered in a sandbox:

1. Stop external access to the affected environment.
2. Preserve internal evidence for review.
3. Remove the data from the sandbox.
4. Rotate exposed credentials or secrets if applicable.
5. Record the corrective action in the release or sandbox evidence folder.
6. Re-run sandbox data safety verification before access resumes.

## Exit criteria for buyer-facing sandbox

A CROWN sandbox is buyer-facing ready only when:

- This policy is satisfied.
- The sandbox landing page clearly separates school, daycare, and camp tracks.
- Guided and self-guided modes are explicit.
- Demo data is visible and resettable.
- Persona login paths are verified.
- Seed packs are deterministic.
- Compliance/customer-readiness blockers tied to sandbox data have been closed or explicitly dispositioned by release authority.
