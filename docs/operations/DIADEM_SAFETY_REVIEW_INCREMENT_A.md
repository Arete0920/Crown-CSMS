# Diadem #595 — default-off safety-review foundation (Increment A)

## Scope and source-only status

The source changes in this branch are **not operational childcare approval or
Delaware licensing certification**. They do not activate any staff coverage,
DaycareSite, DaycareRoom, enrollment, release, payments, Azure resource or tenant.

The existing proposal endpoint, `DaycareRoomStaffCoverage`,
`daycare_checkin.py` and `daycare_release.py` are deliberately unchanged.
This increment adds separate, append-only **evidence review** records.

The review API additionally requires an explicit
`diadem.daycare.safety_review` Crown permission as well as the existing
director-only, tenant-bound `diadem.daycare.configure` authority. **No
permission/role seed is added.** In default deployment all new endpoints deny
writes and reads until an independently authorized role-permission configuration
is approved. Do not grant this permission in a production childcare tenant
based only on a role title.

## Evidence stages

1. The existing PR #654 creates an inactive staff proposal, with proposal
   audit, staff identity and interval.
2. A separately attributed qualification review references the staff/site,
   external authority and evidence reference, category, decision, effective
   interval and optional predecessor. A determination cannot be inferred from
   a uploaded filename or role.
3. A room-policy review references the site/room, jurisdiction, facility license
   reference, policy version, age range, group-size/ratio inputs, source, decision,
   effective interval and optional predecessor. These fields are review
   documentation, **not verified jurisdictional rules or a live ratio engine**.
4. An assignment planning review references the existing proposal, qualification
   review and policy review. An APPROVED planning decision requires both current
   prior reviews to cover its whole interval; even this does not mark staff
   qualified, on duty or active.
5. Readback is school/site/room scoped, attributed, timestamped and always
   declares `operational_activation: false`. Reviews remain append-only;
   corrections/revocations create a new record referring to the predecessor.

Review evidence must not include raw background checks or sensitive documents.
Retention/access-control requirements for those records remain separate work.

## No operational bridging

There is intentionally no method that writes any of the following:

- `DaycareRoomStaffCoverage.is_active`
- `DaycareRoomStaffCoverage.is_qualified`
- `DaycareRoomStaffCoverage.qualification_evidence`
- `DaycareRoom.policy_verified_at`
- `DaycareRoom.is_active`

No policy table in this increment changes check-in, ratio, custody or release
authorization. The new reviews cannot be counted as real onsite supervision.

## Source verification and unexecuted gates

The new test scope is
`backend/aftercare/tests/test_daycare_approval.py`. It covers default-off
authorization, forged fields, tenant boundaries, idempotency, attribution,
revocation, policy mismatch, rejection of stale evidence, rollback on audit
failure, and lack of operational activation. The existing PostgreSQL safety
workflow includes the file and enforces an unskipped two-connection review race
case. Existing custody and staff-proposal tests remain intact.

Source commit and Django model/migration checks must be executed in an
appropriately isolated environment before any proposal to merge. This branch
does **not** certify test execution or historical CI parity.

Required post-authorization verification in a disposable PostgreSQL test
environment (never a live childcare database):

- Python compilation and Django `manage.py check`.
- `makemigrations --check --dry-run` to detect missing model changes.
- New tests and existing Diadem check-in, release, staff proposal and visit
  foundation regressions using a fresh synthetic database.
- PostgreSQL JUnit mandatory unskipped race case.
- Migration plan review and backup/restore rehearsal **only after a separate
  explicit authorization to apply a migration**, even to a disposable database.
- Current-source and final-head CI/repository-policy checks if a PR is later
  approved.

## Outstanding product-owner/jurisdiction decisions

Independently establish actual Delaware facility license/category/conditions,
applicable current sections 24, 27 and 28 of Title 14 Code 933, external
eligibility and background-check determinations, reviewer qualifications,
on-premises supervision rules, current valid age/group-size rules, expiry and
evidence privacy controls. The director's app role is not evidence of legal
authority. Never default a ratio or certify childcare based on synthetic data.

## Recovery

Before migration, reverting this isolated branch is source-only: there are no
new database tables or changed custody rows. After an approved future
migration, additive new review tables must be preserved for audit and historical
readback; remove the API/permission instead of deleting review or custody data.
Any physical operational activation remains a separate change with its own
backup/restore, backward compatibility and open-custody exit policy.

Do not merge this branch, dispatch workflows, run migrations, activate coverage,
or modify Azure without separate authorization. #427 and #617 are independent.
