# Owner handoff: universal fictional presenter on existing DEV

Status: SOURCE ONLY. No Azure resource/settings/data changes, live provisioning,
credential rotation or database migration was performed for this assignment.
This is an explicit future owner operation. Do not activate while prerequisites
or unsupported-workflow acceptance remain unresolved.

## Readiness and isolation

| Workflow | Implemented source acceptance | Remaining release evidence |
|---|---|---|
| Administration | Reused 703 fictional students, families, school/year/rosters and finance samples; ordinary principals | Owner presenter dashboard transactions and hosted readback |
| Aid | Parent submit; canonical profile; officer review/wizard offer; real noncash approval, budget and ledger; idempotency; parent readback | Exact deployed browser/reload and PostgreSQL evidence |
| SGO | Explicit fictional program applicant/processor grants; submit/retry/correction/resubmit; immutable audits | Exact deployed scope/revocation acceptance; no SGO funds or membership authority |
| Daycare | Existing fictional policy/staff/custody seed; real admission API, roster and release; role/tenant/expiry denial | Presenter browser and PostgreSQL custody concurrency acceptance |
| Before/After/Extended Care | Verified Reed household, independent AM/PM records, staff handoff and pickup; zero-priced assessment | Presenter browser and PostgreSQL custody acceptance |
| Camp | Real configuration create/update; existing registration; blocked admission and parent readback | Full forms/health/pickup clearance has no complete public mutation path; READY custody unsupported |
| Academics/portals | Normal teacher/student/parent login; assignment, draft/submit, feedback, reload, retained-history classroom archive | Hosted exact-source acceptance |
| Admissions/enrollment | Existing school enrollment templates and product workflows inventoried | Universal prospect/admission-to-enrollment functional acceptance incomplete |
| Finance | Fictional obligations/invoices and real noncash Aid credit/budget transactions | Wider receivables/finance presenter acceptance incomplete; no live payments |

The reserved school is `cd216908-b692-5fa7-997b-743f811f1ea9`, absent from the
public catalog. Usernames are `presenter.<school UUID without dashes>.<persona>
@fictional.crown.invalid` (one uninterrupted address). Original Heritage UUID
`19801b59-8c05-4c84-9312-5d792e4e839d` is never provisioned, reset or copied.
No real school/customer information or local SQLite file is imported. ORM
fictional generators construct independent records. No buyer invitation or
SandboxBuyerWorkspace is created. Prospect workspaces remain a separate lane.

## Preconditions the owner must verify

1. Review and merge the prerequisite source PRs through protected-main checks
   and the approved review process. Record the final immutable 40-character
   source SHA and compatible frontend artifact SHA. Green source checks are
   not deployed acceptance or independent human review.
2. Separately authorize DEV deployment/configuration and fictional tenant
   provisioning. This assignment does not authorize executing these steps.
   Use the existing `crown-api-dev.azurewebsites.net` app and existing approved
   Azure PostgreSQL database. No new service, plan, database or recurring cost.
3. Use the existing DEV deployment procedure for that exact revision. Disable
   automatic schema mutation. Run `python manage.py migrate --check` only as a
   read-only compatibility check. Pending migrations require separate approval;
   stop rather than applying them under this handoff.
4. Confirm normal role catalog grants already exist. The preflight checks Aid,
   school administrator and Daycare authority and refuses an incomplete catalog.
   It never installs global grants. Do not run `seed_permissions` in shared DEV
   merely to make this preflight pass; catalog changes require their own review.
5. Confirm owner-approved existing backup/recovery coverage and current live
   tenant isolation. Do not point this command at another host/database or a
   production database. Verify actual runtime identity and database hostname.
6. Owner-enable both `CROWN_UNIVERSAL_PRESENTER_ENABLED=true` and
   `CROWN_UNIVERSAL_PRESENTER_APPROVED_SHA=<exact approved deployed SHA>` on every
   participating existing DEV app/worker process. Preserve DEBUG=false,
   CROWN_ENV=dev, CROWN_DEMO_MODE=false, CROWN_SANDBOX_ALLOW_OPEN_SESSION=false,
   and CROWN_SANDBOX_OUTBOUND_DISABLED=true. This is a separately authorized
   configuration change, not something this assignment executes.

## Exact read-only preflight

In the existing owner-authorized DEV application terminal, in the directory
containing `manage.py`, set the approved source value and run:

```sh
EXPECTED_SHA='OWNER_APPROVED_40_CHARACTER_SHA'
python manage.py migrate --check
python manage.py provision_universal_presenter --expected-sha "$EXPECTED_SHA"
```

The placeholder deliberately fails the source guard. Supply the actual approved
revision. Preflight must report `PRECHECK_ONLY`, the reserved school ID and
`release_certified=false`. It creates no school, accounts, modules or grants.
If the reserved ID exists without trusted command provenance, or belongs to a
buyer workspace, stop. Never adopt or overwrite that school.

## Exact separately approved apply

Initialize the nine *new* fictional principals only if normal password login is
approved. Supply distinct strong 20–256 character secrets through the owner's
existing secret-delivery process for these environment variable names:

- CROWN_PRESENTER_SCHOOL_ADMIN_PASSWORD
- CROWN_PRESENTER_ADMISSIONS_DIRECTOR_PASSWORD
- CROWN_PRESENTER_FINANCE_DIRECTOR_PASSWORD
- CROWN_PRESENTER_DAYCARE_DIRECTOR_PASSWORD
- CROWN_PRESENTER_DAYCARE_STAFF_PASSWORD
- CROWN_PRESENTER_TEACHER_PASSWORD
- CROWN_PRESENTER_PARENT_PASSWORD
- CROWN_PRESENTER_STUDENT_PASSWORD
- CROWN_PRESENTER_BOARD_PASSWORD

Never paste values into tickets, logs, command arguments or committed files.
Existing usable credentials are refused; no credential rotation is performed.

```sh
python manage.py provision_universal_presenter \
  --expected-sha "$EXPECTED_SHA" \
  --confirm-school-id cd216908-b692-5fa7-997b-743f811f1ea9 \
  --enable-password-login --apply
```

All school/persona/family, care and Jireh fixture writes commit in one database
transaction. Failure rolls them all back. Repeated apply refuses an existing
presenter. Without `--enable-password-login`, new credentials remain unusable;
there is no public demo token issuer or automatic password reset. The command
calls no Azure API, schema migration or payment provider. The service independently
rechecks seven-day exact-school care entitlements; reseeding never renews them.

## Activation acceptance and approved updates

Owner acceptance must compare backend `/api/health/` and frontend `/build.json`
against the approved source and actual database state, then use normal login.
Exercise the transactions and independent reloads listed in the table with their
actual principals. Test unauthorized roles, expired/revoked authority, foreign
school IDs and a separate prospect workspace. Verify persisted downstream budget,
ledger, audit and custody results. Do not report full five-module readiness while
Camp clearance, admissions or full replay remain incomplete. Local browser
harnesses intentionally accept loopback origins only; they do not certify Azure.

For an application update, first verify compatible schema and run all relevant
source/functional/security tests. Deploy only an approved compatible revision,
then separately update the approved-SHA setting and repeat deployed acceptance.
A mismatch blocks presenter-specific provisioning and Jireh operations. Do not
reseed an existing presenter, rotate its credentials or automatically renew care
terms. Existing normal application authorization remains authoritative.

## Reset and retention contract

The only implemented repeat/reset boundaries are guarded bootstrap reset before
protected module state exists and academic classroom archive retaining immutable
submissions, grades, principal IDs and credentials. For owner-approved hosted
academic replay:

```sh
python manage.py provision_universal_presenter \
  --expected-sha "$EXPECTED_SHA" \
  --confirm-school-id cd216908-b692-5fa7-997b-743f811f1ea9 \
  --archive-classroom --apply
```

This unpublishes only the owned presenter's assignments with normal model
validation; it does not delete care, financial or SGO history. Use new assignment
names for subsequent exercises. Historical immutable submission revisions remain.

Whole-environment replay is a remaining design/implementation gate. The intended
retention-safe design is a serialized owned-generation rollover: expected-current
UUID/source/idempotency key; new deterministic fictional tenant/user IDs generated
from templates; no copy from the prior database records; refuse unresolved live
custody; retire only owned principals after checking foreign role associations;
retain historical financial/custody/SGO records; quarantine every generation; and
publish the new current-generation binding only after complete atomic success.
It requires a reviewed registry, race/retry/foreign-reference tests, explicit
principal/portal routing and deployed PostgreSQL proof. No command here implements
or claims that rollover. Never truncate shared tables or delete immutable history.

## Containment and rollback

On a scope or state mismatch, stop the demonstration and disable new presenter
access using the established owner-authorized school/account suspension procedure.
The feature flag disables the added realm and provisioning, not every normal
application endpoint. A source revert alone does not revoke already issued normal
credentials or remove records. Preserve audit evidence; use the approved recovery
process for any data correction. Never reset a customer school or the original
Heritage tenant to repair the fictional presenter.
