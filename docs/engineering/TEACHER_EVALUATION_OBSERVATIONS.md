# Teacher Evaluation — Unscored Observation Slice (#642)

Status: **Draft source, not certified.** This additive implementation intentionally does **not** establish a complete formal teacher evaluation, rubric, summative rating, teacher growth plan, professional development attendance verification, or third-party evaluation interoperability.

## Existing identity and privacy contracts

- Canonical evaluated staff is `core.Staff` with `role_type=TEACHER` and active status when a cycle is created. Login identity is `core.UserAccount.staff`, never a name/email heuristic. `hr.Employee` is not used.
- The evaluation cycle belongs to one `core.School` and one `core.AcademicYear`. All relationships validate tenant ownership, and all API routes require an explicit `X-School-Id` matching the logged-in school.
- Exactly one designated evaluator is assigned per teacher/cycle in this initial version. New assignments require an active school-bound account with the independently granted `evaluation.observe` permission.
- School administration and evaluator authority are **not** inherited from `hr.view`, `hr.edit`, `pd.view`, `classroom.view`, `is_staff`, or `is_superuser`. The initial permission seed registers capability names but grants **none** to any default role.
- Restricted capability names are `evaluation.assign`, `evaluation.observe`, `evaluation.read_assigned`, `evaluation.read_self`, and `evaluation.respond_self`. Test fixtures create both necessary grants; production entitlements remain disabled until approved school-level authorization procedures exist.
- **Critical activation restriction:** `RolePermission` remains global by role code; the new append-only `TeacherEvaluationAccessEvent` adds the missing school/user/capability barrier. There is **no public grant/revoke endpoint** and no approved live entitlement provisioner or separation-of-duties authority. Test-only event insertion must not be treated as production authorization. Personnel policies and authorization administration still block live activation.
- All evaluation API responses, including private observation narratives, set private `Cache-Control: no-store` using Django's never-cache response wrapper. Test readback checks response headers.
- Each evaluation read or write requires **both** its existing school-scoped role capability and an explicit most-recent `grant` access event for the same school, individual account, and capability. A later `revoke` denies subsequent requests, even where the shared role still carries the capability.
- Subject teachers see only their submitted observations; designated evaluators can see their own drafts. Other staff, unrelated evaluators, students, parents, board, and unrelated HR personnel are excluded. Acknowledgment records receipt, not agreement.

## State transitions and audit

- `POST /api/v1/teacher-evaluations/cycles/`: create a school/year/teacher cycle and designated evaluator; one cycle per teacher and year in this initial slice.
- `GET /api/v1/teacher-evaluations/cycles/`: limited, school-scoped list with per-actor filtering.
- `GET /api/v1/teacher-evaluations/cycles/<uuid>/`: subject/evaluator details with bounded `offset` pagination (100 observations/page, `observations_total` and `observations_next_offset`). Pagination and totals apply **after** school and viewer filtering; drafts are excluded from a subject teacher's views and counts.
- `POST /api/v1/teacher-evaluations/cycles/<uuid>/observations/`: create unscored private observation draft with evidence narrative and school-year-valid timestamp.
- `POST /api/v1/teacher-evaluations/observations/<uuid>/submit/`: publish a draft to the subject teacher; version-checked and final.
- `POST /api/v1/teacher-evaluations/observations/<uuid>/responses/`: subject-only receipt acknowledgment or disputed statement; one response per observation.
- All writes require actor-scoped UUID request keys. Duplicate key/payload replays do not duplicate events, while changed payloads and stale versions return conflict. The action, record IDs, before/after **metadata**, timestamp, school, and actor are retained in `TeacherEvaluationEvent` without copying confidential observation prose into the general event snapshots.
- QuerySet bulk writes and deletion are prohibited through normal model APIs. The only permitted observation update is draft-to-submitted; submitted observations and teacher responses are append-only at the ORM workflow layer. Raw SQL/DB administrators remain outside this ORM boundary; this is **not** a cryptographic or database-trigger immutability claim.
- All state mutations and their event history run in transactions. PostgreSQL locking/retry correctness remains subject to CI verification.

## Known limitations and policy decisions

- **No observation narrative amendment in v1.** A versioned correction procedure that retains both old and new content must be designed and reviewed before enabling it.
- **No rubric, weighted criterion, employment consequence, comparative teacher ranking, personal faith score, or automated employment decision.** No third-party copyrighted rubric is included.
- **No attachment, classroom-video, student data import, confidential classroom-coaching import, mass export, cross-tenant aggregate, or personnel record transfer.** All input is structured and bounded.
- The response API's idempotent replay returns stored response **metadata** (without confidential teacher comment text); clients can read full authorized comments through the cycle detail route.
- School policy for personnel privacy, retention, grievance/dispute resolution, evaluator recusal, legal hold, and signatures remains **OPEN**. A first-slice feature cannot be marked suitable for live school personnel records without these decisions.
- School-managed activation is deliberately absent. The presence of code in source does not authorize deployment or any user role grant.
- Source code alone is not test, deployment, or personnel-policy certification. Preserve exact-source CI, migration, PostgreSQL and independent review evidence for each revision. Browser verification, live customer permissions, hosted SHA parity and school-level policy approval remain separate requirements.

## Required acceptance

Run `python manage.py check`, `python manage.py makemigrations --check --dry-run`, and the focused `backend/teacher_evaluations/test_observations.py` tests on PostgreSQL in the repository's governed environment. Confirm school A/B isolation, teacher A/B isolation, HR-only denial, evaluator revocation, missing-tenant denial, exact-key replay and conflict, duplicate cycle/response denial, submitted-record immutability, no unapproved grants, and independent saved GET/reload behavior. Extend the first slice with real authenticated Playwright teacher/evaluator flows **before** labeling the frontend implemented.

Do not merge this draft until exact-head checks, migration/schema checks, code review, and the separate personnel policy questions have acceptable evidence. Keep #617 / #427 and the enrollment/demo PRs as separately owned work.
