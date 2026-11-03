# Jireh SGO — local fictional partner-intake acceptance slice

**Status:** Source-only development slice. It is not a partner-approved, public-family, Azure, regulatory, or payments capability. Historical issue [#182](https://github.com/Arete0920/Crown-CSMS/issues/182) remains the product-scope authority. Arete processes *for* independent SGOs; Arete does not operate an SGO.

## What the slice does

- Preserves existing `SGOOrganization`, `SGOProgram`, and `SGOApplication` records. The application's program is the canonical organization boundary.
- Adds explicitly provisioned `SGOFamilyGrant` (user + program + opaque synthetic student/school keys + consent version) and `SGOProcessorAssignment` (user + program). **Neither derives from school roles, superuser, SGO membership, SGO ADMIN, or SGO REVIEWER.**
- Captures a strictly bounded grade and versioned demonstration consent, persists it against the existing application, and exposes a private readback across sessions. Repeated submissions with the same UUID4 key return the original application without another audit event; conflicting requests return HTTP 409.
- Allows only an explicitly assigned processor to request one of three non-sensitive correction reasons. The family can correct/resubmit under optimistic revision and UUID4 retry protection; events carry only a revision and fixed reason.
- Holds application eligibility at `UNREVIEWED`; no eligibility determinations, final SGO award decisions, donations, committed funds, disbursements, or attachments are created by this intake path.
- Ensures all listed, read, or mutated cases are restricted to a current per-program family grant or processor assignment. All successful response payloads are marked `Cache-Control: private, no-store`.

## Hard runtime boundary

This feature requires **all** of the following:
- `CROWN_SGO_FICTIONAL_INTAKE_ENABLED=true` (default false)
- `DEBUG=true`
- `CROWN_ENV=local` and `DJANGO_ENV=local`
- No `WEBSITE_HOSTNAME` or `WEBSITE_INSTANCE_ID`
- `CROWN_DEMO_MODE=false` (ordinary Django demo mode intentionally blocks writes)

Django's tenant middleware grants schoolless routing only to exact fictional family/processor paths while this gate holds; the API separately rechecks runtime, rejects caller-supplied school headers, and requires an authenticated, active principal with the specified grant. The frontend schoolless transport is restricted to exact routes and methods when `VITE_LOCAL_DEMO=1`. These conditions are not partner authentication or a future production authorization design.

## Reproducible isolated Heritage demonstration

Use a *fresh reviewed and merged local source revision*, not an outdated installer pin. On the development laptop:

1. From repo root, run `py scripts/demo/start_heritage_local.py --prepare-only` (or `python` on POSIX). The script installs dependencies if necessary, migrates the isolated Heritage SQLite database, runs the current Heritage seed and proof gate, and seeds two synthetic partner SGOs.
2. Read `.local-backups/heritage-demo/sgo-credentials.txt` locally. Account passwords are generated anew on preparation and written to a mode-0600 file **outside Git**. The six accounts are fictional partner admin, family, and delegated processor accounts for each of Delaware and Pennsylvania. Never copy this file into a PR or transcript.
3. Start `py scripts/demo/start_heritage_local.py`. Open `http://localhost:4173/jireh-sgo/intake` (the launcher also opens the usual sandbox page). Sign in through the application's existing login flow using the synthetic Delaware family account.
4. Select the Delaware fictional partner and program; select grade, affirm the displayed demonstration consent version, submit, and verify the **saved application ID, revision, and consent date**. Reload or sign out and back in: the application should read back from the database.
5. Sign out and sign in as `sgo_demo_de_processor`. Open the same intake route; select Delaware, refresh its case queue, and request a non-sensitive correction. This records a request, **not a scholarship decision**.
6. Sign back in as `sgo_demo_de_family`, reload the same case, update or confirm the fictional grade, and resubmit. Verify status `RESUBMITTED` and incremented revision.
7. Repeat with the Pennsylvania family and processor. The Delaware accounts must not list or access Pennsylvania records (and vice versa). The partner ADMIN account alone must not submit family intake or operate the processor queue.

If this local demo cannot authenticate the seeded accounts through the existing login flow, **do not claim a certified demonstration**. Diagnose the existing login/sandbox role-routing contract without enabling unauthenticated endpoints.

## HTTP contract

- `GET /api/v1/jireh-sgo/family/programs/` — only active explicit family grants, with current application IDs
- `POST /api/v1/jireh-sgo/family/submit/` — `{program_id, grade_level, consent: true, consent_version, submission_key: UUID4}`
- `GET /api/v1/jireh-sgo/family/applications/<uuid>/` — family-authenticated durable readback
- `POST /api/v1/jireh-sgo/family/applications/<uuid>/correct/` — `{expected_revision, grade_level, correction_key: UUID4}`
- `GET /api/v1/jireh-sgo/processor/programs/` — explicit delegated processor assignments
- `GET /api/v1/jireh-sgo/processor/programs/<uuid>/queue/` — partner-program-scoped cases
- `POST /api/v1/jireh-sgo/processor/applications/<uuid>/request-correction/` — `{expected_revision, reason, request_key: UUID4}`

The correction reason is one of `GRADE_UNVERIFIED`, `PROGRAM_DETAIL_MISMATCH`, `OTHER_NON_SENSITIVE`. Request bodies reject unknown fields, including unintended PII/document data.

## Verification required before merge

Run from the repository:

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest jireh_sgo/tests/test_services.py jireh_sgo/tests/test_read_only_api.py jireh_sgo/tests/test_fictional_intake_api.py -q
cd ../frontend/dashboards
npm ci
npm test -- src/pages/JirehSGOIntakePage.test.jsx src/pages/JirehSGODashboard.test.jsx
npm run build
```

CI and a genuine browser replay from a fresh local database are independent acceptance gates. Do not equate source, seeded fixture presence, or five-module preflight with functionality.

## Open partner/production dependencies

Signed partner processing and data-sharing authority, adult/family identity proofing, real SGO program selection and published policies, legally reviewed consent, secure upload/document screening, school-to-student authority mapping, retention and privacy notices, audited partner-controlled final eligibility/award/appeal decisions, accessible household UX, and approved source-of-truth integration remain **not implemented**. The fictional local flags, credentials, and synthetic grants cannot be reused as live partner authorization. No Azure or production deployment, live partner provisioning, payments, or fundraising is authorized by this slice.
