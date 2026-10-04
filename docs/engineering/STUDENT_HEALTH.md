# Restricted student health workspace

## Ownership and recorded evidence

The health and health-office dashboards add a live chart referencing canonical
`core.Student`, `core.Guardian` and the selected school. The clinical domain owns
visits, medication authorization and administration records, immunization evidence,
care-plan evidence, follow-up dates, corrections and audit reasons. It does not write
student identity, household relationships, attendance, grades, billing or payments.
Existing dashboard templates retain their preview boundaries.

Each entry records the actual timezone-aware event time, observations or transcribed
source details and a reason. Future events and dates before the student's birth are
rejected. Immunization and care-plan entries require an evidence reference. The
workspace records reviewed facts; it does not diagnose, prescribe or determine
immunization compliance. Source documents remain in the authorized document system.

Medication authorization requires reviewed order and consent references, directions,
route, a positive documented dose and unit, inclusive start/end dates, and explicit
staff verification of guardian authority. The guardian must belong to the student's
canonical school/family and have an explicitly clear custody flag. Unresolved flags
block new authorizations and administrations. Revocation remains available after
family/authority changes and retains the original order evidence.

Given administrations must match the documented dose and unit exactly. No automatic
dose calculation, unit conversion, dosing suggestion or medical advice is provided.
Refused and not-given entries cannot include an administered dose. Actual event time
must fall within authorization dates in the school timezone and precede any revocation.
Birth-date and follow-up comparisons use the same school calendar; invalid timezones
fail closed. Historical events
may be recorded against a subsequently revoked order when they predate revocation;
current guardian authority must still be verified. School policy and qualified staff
remain responsible for reviewing source records and the actual administration.

## Access and corrections

Dedicated persistent school-scoped `student_health.view` and `student_health.edit`
permissions separate clinical reads and writes. Initial grants are limited to nurse
and health-office role codes. Generic system-status `health.view`, administrative,
parent and teacher access do not grant clinical access. Requests require an explicit
school header; inactive accounts fail closed. No clinical records appear in family,
teacher, communication, reporting or general system-health responses.

Entries and mutation evidence are append-only. Corrections retain school, student
and kind, link to the original entry and preserve the reason and actor. An entry can
have one direct correction; further corrections target the latest entry. Medication
orders are immutable except for reasoned, versioned revocation. Bulk updates and
deletes are blocked. Canonical student and guardian rows are locked while reviewing
medication authority; patient and actor locks serialize chart writes and retry keys.

Inactive students retain readable history and may receive corrections, but cannot
receive new chart entries or authorizations. Counts exclude superseded entries while
the chart retains them. Chart, authorization and audit histories have 100-row pages.
Student choices are bounded to 200 with search and full counts. Follow-up counts
cover all current entries whose recorded follow-up date is due; they are a staff
review queue, not proof that follow-up was completed or a notification was delivered.

## Validation and rollback

Tests exercise permission and tenant boundaries, canonical patient/guardian identity,
invalid time/dose/evidence, retry conflicts, stale revocation, custody changes,
authorization periods, exact source units, refusal records, retained corrections,
read-only access, full counts/pages and inactive students. Interface tests exercise
canonical patient selection, actual observations, correction identity, retry retention,
read-only controls, pagination and removal of stale patient charts.

The schema is additive. Revert code to stop new writes and retain the clinical tables
and audit evidence; do not reverse migrations destructively after records exist.
Permission migration reversal retains grants, while code removal removes the route.
Repository verification does not establish deployed operation, external source-document
access, school clinical-policy acceptance or legal compliance certification.
