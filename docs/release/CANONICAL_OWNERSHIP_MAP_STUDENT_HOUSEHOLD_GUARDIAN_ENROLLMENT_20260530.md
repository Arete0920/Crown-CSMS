# Canonical Ownership Map - Student/Household/Guardian/Enrollment (2026-05-30)

Purpose: define single-writer canonical ownership for student spine entities and mark legacy duplicates as read-only/transitional.

## Canonical Owners

| Domain Entity | Canonical Owner | Write Authority | Read Compatibility | Notes |
| --- | --- | --- | --- | --- |
| Household | households.Household | households app only | core.Family transitional read-only | `households.models.Household` is canonical tenant-scoped household spine. |
| Guardian | households.Guardian | households app only | core.Guardian transitional read-only | `households.models.Guardian` is canonical guardian identity. |
| Student | households.Student | households app only | core.Student transitional read-only | `households.models.Student` is canonical student record spine. |
| Enrollment (section-level) | academics.Enrollment | academics app only | core.Enrollment transitional read-only | `academics.models.Enrollment` is canonical roster/section membership. |
| Enrollment (year-level historical) | core.Enrollment (legacy) | frozen (no net-new writes) | read-only for migration/backfill | Legacy historical surface; no new canonical writes. |

## Controlled Overlaps

- core.Student (legacy mirror; no net-new writes)
- core.Guardian (legacy mirror; no net-new writes)
- core.Family (legacy mirror; no net-new writes)
- core.Enrollment (legacy mirror; no net-new writes)

## Guardrail

- Any net-new write workflow touching student/household/guardian/enrollment must target canonical owners above.
- Legacy core mirrors remain allowed only for compatibility reads and controlled migration backfill.
