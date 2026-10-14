# Jireh SGO: isolated noncash foundation

**Status:** Engineering proposal for governed merge. No standalone product, legal certification, partner approval, external identity, SGO API or live funds.

The separately authorized organization domain reuses the existing CROWN user identity, but does not reuse school authority. An active organization and explicit active viewer/reviewer/admin membership are mandatory. Staff or superuser privileges are never an SGO bypass. Organizations and memberships default inactive.

Programs record organization, academic calendar year, source and immutable eligibility policy version. Federal/state source labels are classifications, NOT eligibility or compliance conclusions. Human attestations accept only literal booleans and opaque UUID4 evidence references. Applications use opaque student/school IDs; these do not confer access to school records or establish consent or enrollment.

Awards are **noncash commitments only**. This slice deliberately has no funded, cleared, allocated, transferred, disbursed or paid fields or operations. Do not call school aid (aid.AidAward), financial_aid.AidAward, ledger payments, or billing allocations from a commitment. Replayed application, program, attestation and commitment operations return existing records without duplicate audit events. Cancellation is idempotent; award amount changes and recommitment after cancellation are prohibited. Relational ownership derives from program to application to award, eliminating contradictory SGO-organization foreign keys.

Audit records use fixed per-action metadata schemas and reject free-form personal data. Normal saves are append-only; database-access restrictions and immutable evidence archive policy require separate operational review.

## Verification

From backend with supported dependencies: 
- python manage.py check
- python manage.py makemigrations --check --dry-run
- python manage.py test jireh_sgo.tests
- exact-head governance checks, security checks, tenant isolation and migration validation

## Remaining issue #182 gates

Partner enrollment; signed sharing contracts; dedicated SGO identity and isolated externally exposed API; student/school mapping; legally reviewed Section 25F and state rules; consent; family need and documents; awards and appeals; separate custody/donor accounting and reconciliation of committed, funded, cleared and allocated amounts; qualified expenses; standalone accessible UI; two-SGO synthetic pilot; operational security approval and release authorization. No live settlement or production access is permitted by source acceptance.
