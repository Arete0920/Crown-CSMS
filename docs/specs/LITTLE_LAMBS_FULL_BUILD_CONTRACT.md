# Little Lambs Full Build Contract

Status: implementation contract created from live repo evidence and product requirements.

## Verified repo baseline

Little Lambs as a separate backend app was previously implemented in PR #628 but was closed unmerged. The current repo also contains a verified Aftercare / Daycare module implementation on branch `feature/aftercare-daycare-completion-20260515_201747`, with backend app `backend/aftercare`, frontend pages, setup wizard, board card, API wiring, and tests passing according to `AFTERCARE_DAYCARE_VERIFICATION_SUMMARY.md`.

This contract treats the existing `aftercare` module as the restoration spine and expands it into the full Little Lambs product surface. Do not create a duplicate `backend/daycare` app. Keep `backend/aftercare` for extended-care primitives and add `backend/little_lambs` only if it is required as a distinct early-childhood domain app with explicit integration boundaries.

## Product definition

Little Lambs is the faith-based daycare, preschool, before-care, aftercare, special-day, holiday-camp, summer-camp, and church-event childcare operating module for Crown.

It must support two deployment modes:

1. Standalone daycare tenant.
2. Integrated Crown school tenant for schools/churches with preschool, daycare, before care, or aftercare.

## Revenue model

- SaaS: $8 per active child per month.
- Payment participation: 1% of processed tuition/payment volume.
- Reference tuition model: $255 per week for 50 weeks = $12,750 annual tuition volume per child.
- Reference platform revenue: $96 SaaS + $127.50 payment participation = $223.50 annual revenue per child before setup/add-ons.

## Core architecture principles

- Use Crown tenant scoping through the canonical household/school resolver. No raw tenant header trust.
- Every query must be school scoped.
- Every write must be audit logged.
- Every API endpoint must be entitlement gated by an active/trial Little Lambs or aftercare/daycare module entitlement.
- Preserve separate early-childhood records from K-12 Student records, but allow optional promotion into Crown K-12.
- Reuse Crown household, guardian, billing wallet, payment method, communications, documents/forms, RBAC, and audit infrastructure.
- Keep childcare-specific records separate: child care profile, care enrollments, rooms, ratios, daily reports, meals, incidents, pickup authorization, licensing/compliance records.

## Required modules

### 1. Setup wizard

Route: `/little-lambs-setup`

Wizard states must follow Crown wizard convention:

`draft -> configured -> care_programs -> billing_rules -> committed -> verified`

Wizard steps:

1. Organization mode
   - Standalone daycare
   - Integrated Crown preschool/daycare
   - Before/aftercare only
   - Church event childcare
2. Rooms and age groups
   - Room names
   - Licensed capacity
   - Age bands
   - Ratio limits
3. Programs and sessions
   - Daycare
   - Preschool
   - Before care
   - Aftercare
   - Before + aftercare
   - Drop-in
   - Special school-closed days
   - Teacher workdays
   - Early dismissal care
   - Holiday camp
   - Summer camp
   - Church event childcare
4. Billing and rates
   - Weekly tuition
   - Monthly rate
   - Daily rate
   - Hourly/drop-in rate
   - Late pickup fee
   - Registration fee
   - Special-day fee
   - Sibling discount
   - Subsidy/third-party payer support
5. Parent onboarding
   - Required forms
   - Pickup contacts
   - Payment/autopay setup
   - Communication preferences
6. Commit and verify
   - Create records idempotently
   - Verify counts by GET
   - Freeze session

### 2. Director dashboard

Required cards:

- Current attendance
- Room ratio status
- Children not checked out
- Open incidents
- Unsigned incident reports
- Missing forms
- Expiring immunizations
- Staff certification expirations
- Today meal counts
- Billing due / failed payments
- Subsidy receivables
- Capacity by room/program
- Upcoming special days
- K-12 promotion candidates

### 3. Classroom dashboard

Mobile-first staff surface:

- One-tap check-in/check-out
- Room roster
- Ratio warning
- Meal logging
- Bottle/feeding logging
- Diaper/toileting logging
- Nap timer
- Mood/activity logging
- Photo note
- Incident/accident quick report
- Medication administration log
- Bible story
- Prayer focus
- Memory verse
- Supplies needed
- Parent note

### 4. Parent dashboard

Parent-facing mobile-first surface:

- Daily child report
- Photos and teacher notes
- Meals/feedings/diapers/naps
- Faith moments
- Messages
- Forms/signatures
- Pickup authorizations
- Payments/autopay
- Statements and tax receipts
- Incident signature and acknowledgment
- Calendar/special-day signup

### 5. Reporting center

Reporting must be first-class, not optional.

Required reports:

- Daily child report
- Meal report
- CACFP claim report
- Accident/incident report
- Medication administration report
- Immunization compliance report
- Ratio compliance report
- Attendance/check-in/out report
- Licensing packet export
- Emergency roster
- Drill log
- Billing/receivables report
- Payment reconciliation report
- 1% processing participation report
- Revenue per child/room/program report

### 6. Safety and compliance

Required workflows:

- Authorized pickup list with ID verification
- Custody notes and pickup restrictions
- Emergency contacts
- Accident/injury report with body location, witness, staff present, first aid, parent notification, director review, parent signature, attachments, and locked/finalized status
- Medication authorization and dose log
- Allergy action plan
- Illness exclusion and return-to-care clearance
- Immunization tracking
- Fire/tornado/lockdown drill logs
- Staff-child ratio snapshots
- Room capacity enforcement
- Licensing inspector read-only export mode

### 7. Financial core

Required workflows:

- Recurring tuition billing
- Autopay
- ACH/card processing hooks
- Failed-payment retry
- Split-family billing
- Subsidy billing
- Church/school scholarship credits
- Sibling discounts
- Registration fees
- Supply fees
- Late pickup fees
- Special-day fees
- Drop-in fees
- Refunds/credits
- Year-end tax statements
- Processor reconciliation
- 1% payment participation tracking

### 8. Enrollment and waitlist

Required workflows:

- Inquiry form
- Tour scheduling
- Waitlist
- Application
- Registration fee
- Digital enrollment packet
- Capacity matching by room/program/age group
- Parent onboarding checklist
- Admissions prefill into Crown K-12 when integrated

### 9. Crown integration

Integrated mode must share:

- Organization/tenant
- Household
- Guardians
- Billing wallet
- Payment methods
- Communications
- Documents/forms
- Staff users
- RBAC
- Audit logs
- Admissions pipeline

It must keep separate:

- Daycare child profile
- Care enrollment
- Rooms and ratios
- Daily reports
- Meal records
- Incident reports
- Pickup authorization
- Licensing records

Required promotion workflow:

`DaycareChild -> Crown admissions prefill -> Student record -> K-12 enrollment -> same household -> same billing wallet -> same parent login`

### 10. Permissions

Minimum roles:

- Director
- Assistant director
- Teacher
- Floater
- Substitute
- Billing admin
- Church admin
- Parent/guardian
- Authorized pickup only
- Licensing inspector read-only
- Crown admin

### 11. Data migration

Import paths:

- Brightwheel export
- Procare export
- FACTS/RenWeb household/family export
- CSV/spreadsheet import
- Manual quick-add

Data to import:

- Children
- Families/guardians
- Authorized pickups
- Rooms
- Staff
- Balances
- Billing plans
- Immunizations
- Emergency contacts
- Forms status

## Suggested implementation sequence

### PR 1: Restore and reconcile existing aftercare/daycare code

- Confirm `backend/aftercare` current state.
- Confirm frontend pages and routes.
- Confirm setup wizard.
- Confirm tests still pass.
- Do not duplicate the app.

Proof:

```bash
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
pytest backend/aftercare -q
npm --prefix frontend/dashboards run build
```

### PR 2: Add Little Lambs product shell and entitlement

- Add product copy, nav grouping, and module activation naming.
- Confirm entitlement compatibility with `little_lambs` and existing aftercare/daycare keys.
- Add dashboard cards.

### PR 3: Reporting center

- Add incident/accident reporting.
- Add meal/CACFP reporting.
- Add daily child report.
- Add ratio/attendance exports.

### PR 4: Financial core

- Add $8/child/month metric.
- Add 1% processing participation report.
- Add recurring care billing rules.
- Add late pickup/special-day/drop-in billing.

### PR 5: Integrated Crown preschool mode

- Add shared household/billing/admissions bridge.
- Add `Promote to Crown Student` wizard.

### PR 6: Parent and classroom mobile completion

- Add mobile-optimized parent and staff surfaces.
- Add forms/signatures and incident acknowledgments.

## Required proof gate before marking complete

- `manage.py check` PASS
- migrations dry-run PASS
- backend tests PASS
- frontend build PASS
- route search PASS
- dashboard surface search PASS
- wizard contract PASS
- tenant isolation tests PASS
- entitlement gating tests PASS
- cross-tenant denial proof PASS
- billing calculation tests PASS
- report export tests PASS

## Non-negotiable completion standard

Do not mark Little Lambs complete unless the repo contains working, tested, routed, entitlement-gated backend APIs, frontend dashboards, setup wizards, reporting center, billing/payment reporting, compliance workflows, and Crown integrated preschool mode.
