# Universal fictional presenter: source gap analysis and implementation boundary

Inspected protected main: `40d3f0a2d0b59f5337451dce5f4be14e9fee6321`, verified
against GitHub remote on November 14, 2026. Owner: Arete0920. Tracking: #617
(local acceptance), #427 (separate hosted acceptance). Open PR inspection found
only dependency updates #658–#661 and #663–#669; no competing presenter PR.
Recent merged #685/#686 and #688–#691 must remain intact. Existing issue reports
are historical evidence, not proof of this candidate or an Azure runtime.

## Source-level reuse and gaps

The source investigation preceding this change found real database workflows,
not a missing application requiring reconstruction. The limiting issue is that
many demonstration adapters encode the shared Heritage tenant or a separately
invited buyer, rather than accepting an independently owned presenter.

| Requested workflow | Existing source to reuse | Universal presenter status in this increment |
| --- | --- | --- |
| Administration, dashboards | `services.py`, `admin_operations.py`, `test_admin_transaction.py` | 700 fictional learners, deterministic families, enrollments, tuition and roles generated; admin workflow adapter still Heritage-specific; dashboard acceptance NOT VERIFIED |
| Jireh Financial Aid intake/review/award | `heritage_module_samples.py`, `aid/family_demo_intake.py`, `aid/hosted_demo_intake.py`, canonical `aid` models | Shared/local and invite-bound implementations exist; universal fixtures and reviewer journey NOT IMPLEMENTED |
| Jireh SGO intake/corrections | `jireh_sgo` local and hosted APIs, `test_hosted_jireh.py`, local SGO Playwright | Keep independent partner organizations, consent and explicit processor grants; presenter adapter NOT IMPLEMENTED; processor award/fund custody is outside supported demo authority |
| Diadem enrollment/attendance/custody | `seed_local_diadem_pickup`, `seed_hosted_buyer_daycare`, `aftercare` custody services | Operational source exists; presenter identity/entitlement/guardian/staff scenario NOT IMPLEMENTED; never infer clearance from a child row |
| Before School Care | AM `CareEnrollment`, aftercare services, `extended-care-local-custody.spec.ts` | Existing AM workflow; presenter fixture/role and browser acceptance NOT IMPLEMENTED |
| After School Care | PM equivalent of AM workflow | Existing PM workflow; presenter fixture/role and browser acceptance NOT IMPLEMENTED |
| Extended Care | Same AM/PM implementation, not a separate invented module | No third fabricated care engine; presenter acceptance NOT IMPLEMENTED |
| Summer Camp | `seed_local_heritage_camp`, `summer-camp-local-readback.spec.ts`, entitled Camp APIs | Existing setup/registration/save/readback; presenter entitlement and date-valid fixtures NOT IMPLEMENTED |
| Admissions/enrollment | `admissions_seed.py`, `admissions_conversion_seed.py`, canonical admissions APIs | Core enrolled students reused; applicant conversion seed and adapter still Heritage-specific; universal conversion NOT IMPLEMENTED |
| Academics/grading/teacher | `academic_seed.py`, canonical academics APIs, teacher transaction tests | Teacher roster, course, section, category, curriculum, lesson reused with explicit school/user inputs; normal login, UI assignment/draft/submission/feedback/reload and parent readback tested locally; numeric grading/downstream readback tested by API; full five-module readiness NOT VERIFIED |
| Parent/student portals | `parent_enrollment.py`, `parent_daily.py`, `student_self_service.py` | Distinct least-privilege principals created; Reed guardian identity reused inside own school; canonical Reed guardian/student account and verified identity bridges implemented; browser submission/feedback/reload tested; legacy Heritage-only shortcut adapters not ported |
| Finance without payments | Core tuition and `FinanceObligation`/`FinanceInvoice`, `finance.py` | Twelve fictional parent obligations/invoices reused; finance demo transaction adapter still Heritage-specific; payment processing never activated |

Keep existing persona definitions and deterministic `fictional_identities.py`.
Do not clone rows out of Heritage, monkeypatch its catalog, relax exact-local
module guards, or change schoolless SGO/tenant middleware to make ports work.
The existing APIs and tests remain the implementation authority. This matrix
identifies implementation portability gaps, not unsupported claims about the
underlying product. Full universal five-module readiness remains **NO-GO**.

## Implemented isolated foundation

`prepare_universal_presenter` is a local-only operator management command, not
an HTTP provisioning/reset API. It uses reserved school ID
`cd216908-b692-5fa7-997b-743f811f1ea9` and
`presenter.<school UUID hex>.<persona>@fictional.crown.invalid` principals.
The original school/catalog and hosted invite workspaces are unchanged.

The shared generator accepts a school specification and explicit personas.
The teacher generator accepts a school and teacher, deriving roster UUIDs in
that school's namespace. Existing Heritage defaults are unchanged. No real
school data is read or copied. Passwords remain unusable by default; platform staff and
superuser privileges are not granted. Ordinary tenant/RBAC controls still
apply. Opt-in `--enable-password-login` initializes only newly generated accounts from
nine distinct `CROWN_PRESENTER_<PERSONA_KEY_UPPERCASE>_PASSWORD` environment
variables (20–256 characters each). It requires `--apply`, refuses incomplete or
reused secrets, prints no credential values and cannot rotate an existing login.
Use CROWN's normal `/login` with sandbox frontend mode disabled; normal password,
JWT, server identity and school-role checks remain authoritative. All nine roles
are seeded; Board and Daycare choices use the same server-verified login policy.
The cold-start authentication correction in prerequisite PR #693 is required;
no special presenter token issuer or open Heritage session is used.

External communications are quarantined for the reserved presenter school even
when host-wide egress suppression is disabled, including users affiliated only
through a school role. This does not claim to quarantine every possible payment
provider: payment-provider configuration and operations must remain disabled.

### Local operator contract

Use a disposable runtime with the repository dependencies and existing schema
already prepared. This assignment adds no migration files and does not apply
migrations or provision schools in Azure. The command checks the **actual**
Django connection pathname:
`.local-backups/universal-demo/universal.sqlite3` from the repository root.
It requires `CROWN_ENV=local`, `DEBUG=True`, `CROWN_DEMO_MODE=False`,
`CROWN_SANDBOX_ALLOW_OPEN_SESSION=False`, and
`CROWN_SANDBOX_OUTBOUND_DISABLED=True`. Conflicting environment/host identities
are refused. Do not point this runtime at the Heritage SQLite file. All
provider integrations must be absent/disabled in the disposable runtime.

From `backend/`, with those settings:

```sh
python manage.py prepare_universal_presenter
python manage.py prepare_universal_presenter --apply
python manage.py prepare_universal_presenter --apply --reset
python manage.py prepare_universal_presenter --apply --enable-password-login
python manage.py prepare_universal_presenter --apply --archive-classroom
```

The first command is read-only. Apply refuses an existing tenant without an
explicit reset. An existing reserved school without command provenance is
never adopted. The command emits counts and IDs, never credentials, and always
reports `release_certified=false`. Inventory is not workflow certification.

### Reset contract and rollback

Reset locks the owned school, refuses buyer binding, requires original command
provenance and executes reset/rebuild in one transaction. An explicit model
inventory is ordered from children to parents. Unreviewed school-owned module
records block reset. Each ORM deletion first inspects cascades, fast deletes
and SET_NULL updates; foreign or unscoped effects abort and roll back the whole
operation. PROTECT references remain authoritative. The school ID survives,
principal IDs are rebuilt, and roster IDs remain school-namespaced. Existing
JWTs cannot authenticate deleted principals. Never reset live custody/audit or
financial records just to improve demonstration repeatability.

`--apply --archive-classroom` is the retained-history reset for academic practice
work: it unpublishes this school's assignments through normal model validation,
retains immutable submissions/grades/revisions, and preserves all passwords and
principals. Parent/student browsers reload the cleared visible workspace. Teachers
retain history; use a new assignment title for the next exercise. Repeat archive
is safe and reports zero newly archived rows. This is not a whole-school or
custody/finance reset. The destructive `--reset` remains correctly blocked once
protected academic history exists.

This is a reset of the implemented foundation only. After new module workflows
are ported, expand the reset inventory only with explicit lifecycle/retention
acceptance. Until then the safe behavior is refusal, not forced cleanup.
Reverting the one source PR removes the command; it does not authorize deletion
of any database. No hosted data rollback is needed for this assignment.

## Acceptance and remaining engineering work

New `test_universal_presenter.py` exercises the real test database and canonical
bearer-authenticated APIs: preflight, duplicate refusal, identity collision,
seed rollback, write/update/independent readback, wrong-role denial, anonymous
denial, foreign header and section denial, reset/rebuild/repeat, foreign cascade
rollback and unconditional communications quarantine. API readback is not a
browser reload claim. Retain existing Heritage seed/cleanup, teacher transaction
and communications suppression regression suites.

Before full five-module universal presentation, port the remaining matrix gaps
through explicit school/principal inputs in governed increments. Retain the new
canonical parent/student identity links; supply canonical Aid family/year/student lineage; two independent
fictional SGO programs and processor assignments; entitled, date-valid care and
Camp fixtures; explicit fictional safety assertions; and owner-restricted access.
Do not reimplement the engines or reuse buyer invites for the presenter.

For **each** workflow require signed-in positive transactions, independent GET,
DB persistence, browser reload, downstream result, foreign-school denial,
wrong-role denial, stale/invalid transitions, and two reset/replay cycles. Custody
requires exactly one final release audit, verified guardian and signed staff;
SGO requires correction/resubmission and cross-partner rejection without award
or fund authority. School counts, screenshots, source routes, or a green Heritage
suite are not universal acceptance. Preserve #617 physical Windows owner-laptop
signoff and #427 hosted acceptance as separate gates.

## Subsequent owner-authorized Azure activation

**There is no safe Azure activation command for this universal presenter yet.**
The new command rejects Azure and PostgreSQL intentionally. Changing flags to
bypass that guard is not an activation procedure. Do not import this SQLite file.
The owner must first accept the missing portability, access, lifecycle and
functional/security work above, then authorize a reviewed PostgreSQL presenter
provisioning lane. It must retain the fixed presenter identity/provenance,
separate evaluation tenants, no public selector, no live payments and no new
recurring infrastructure. No schema change is implied or authorized here.

For the existing **separate prospect/buyer** lane only, the exact existing
operator sequence after separate owner authorization is:

1. Resolve current protected `main` again; verify required checks and recovery/
   immutable rollback receipt. Record one accepted 40-character source SHA.
   Reuse the existing read-only DEV migration inventory workflow; keep all
   `apply_reviewed_*` options false. Stop on pending or unexpected schema.
2. Reuse `deploy-dev.yml` for existing DEV backend code-only delivery and
   `deploy-dashboard.yml` for DEV-certification frontend with
   `dev_certification_preview=true`, `dev_deploy_only=true`,
   `dev_hosted_jireh_preview=false`, `dev_source_sha=<accepted SHA>`.
   Follow their current contracts; this document never authorizes dispatch.
   Verify backend health/artifact SHA and frontend `build.json` match the SHA,
   CORS and anonymous denial. Do not activate recurring automatic delivery.
3. Close open sandbox sessions, retain exact-source hosted feature gates and
   provision only an explicitly approved, bounded, private buyer invitation.
   Feed the invite ID over stdin to existing operator commands, never in args
   or committed evidence. Confirm required care personas are explicitly invited.
4. In the existing DEV runtime, run read-only preflights in order:
   `provision_hosted_buyer_workspace --expected-sha <SHA> --invite-stdin`,
   then (after separately approved empty workspace creation)
   `seed_hosted_jireh_buyer --expected-sha <SHA> --invite-stdin`,
   `provision_hosted_buyer_care_entitlements --expected-sha <SHA> --invite-stdin`,
   `seed_hosted_buyer_daycare --expected-sha <SHA> --invite-stdin`.
   Each `--apply` is a separate, owner-authorized database mutation, in that
   order; verify preconditions after each. These commands bind **buyers**, not
   the universal presenter. They are not interchangeable with local seeders.
5. Complete separately required AM/PM and Camp fixtures through supported
   authorized product APIs, then execute the seven canonical hosted cases in
   `frontend/dashboards/tests/certification/buyer-sandbox-browser-authority.spec.ts` using their
   current exact-source environment contract. Read that test's current setup
   before execution. The existing public precheck
   `scripts/ops/verify_hosted_buyer_sandbox.py --expected-sha <SHA>` is read-only
   and cannot certify any authenticated workflow. No invitations may be sent
   based solely on its success.
6. Record exact deployed/source SHA, environment identity, tenant and role
   boundaries, persisted transactions, independent reload/readback, downstream
   state and negatives. Keep buyer release NO-GO until all required cases pass
   and the owner signs off. Never close #427 or #617 from source tests alone.
