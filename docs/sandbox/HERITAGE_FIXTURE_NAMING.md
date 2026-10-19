# Heritage sandbox fixture naming

The Heritage Christian Academy demonstration is a fictional school, not a directory
of real people. No fixture identities may be reused for school onboarding, family
communications, or third-party payment or identity testing.

## Business identifiers

| Record | Standard | Treatment |
| --- | --- | --- |
| Tenant | `school_id` (UUID) | Keep the existing canonical tenant identifier |
| Student | `student_number` (`HCA-0001` format in Heritage) | Preserve existing stable keys; do not use a student's name as an identifier |
| Household / family | `<Surname> Family` | Add guardian-first-name disambiguation only for independent same-surname households |
| Guardian | First name, surname, guardian relationship | Use fictional person names, not `Guardian001 Demo` |
| Guardian contact | `first.last.NNN@heritage.example.org` | Reserved documentation domain; never deliver email |
| Student name | Distinct plausible first and family surnames | Keep family linkage and stable student number |
| Telephone | `302/410/610-555-01xx` | Reserved fictional North American numbers; never dial |
| Tuition | `annual_amount_cents`, `net_annual_cents` | Integer minor units, no formatted currency in calculations |
| Academic year | `2026-2027` | Explicit school-year value; separate from record IDs |
| Admission status | Existing canonical status enum | Use sanctioned business workflow states; do not rename contract values |

## Data controls

- `sandbox_demo.fictional_identities` supplies deterministic profile values
  for 286 fictional Heritage families and 700 learner first names. It does not
  read production identity data.
- The authoritative Heritage seed in `sandbox_demo.services.seed_heritage_flagship`
  retains existing school, student, and enrollment keys. Reseeding without a
  reset upgrades earlier generic family and guardian labels in place.
- Only the Heritage sandbox seed uses these identities. They are not default
  field values for migrations, production serializers, or public API responses.
- Preserve historical migrations and existing contract keys. Real business
  name changes require versioned, tenant-scoped data migrations with backfills
  and documented compatibility.
- Use functional metrics such as `applications_submitted_count`,
  `accepted_applications_count`, `students_enrolled_count`,
  `tuition_billed_cents`, `aid_awarded_cents`, and
  `accounts_receivable_cents` in new APIs instead of generic
  `item_count`, `value`, or `metric1`. Existing API contracts are not
  renamed by this fixture-only correction.
- Do not treat synthetic email addresses, phone numbers, financial transactions
  or application outcomes as production evidence.
