# CROWN buyer-diligence workflow acceptance — October 28, 2026

**Purpose:** A bounded, evidence-driven internal rehearsal for licensing/acquisition diligence. This is an **acceptance worksheet**, not a customer demonstration approval, production release, SOC 2 attestation, payment authorization or access grant.

**Source checkpoint at initial preparation:** protected `main` commit `2ae0c7a6283f566fa8918e43e61669dd2fa2d30a` (merged aid reversal correction [#519](https://github.com/Arete0920/Crown-CSMS/pull/519) / closed [#517](https://github.com/Arete0920/Crown-CSMS/issues/517)). Resolve `main`, the selected release-candidate SHA and exact-head CI again at execution; this is not a permanent live identity. No immutable successor production release or new release tag is asserted.

**Commercial boundary:** Buyer-specific access and credentials remain **deferred until signed agreement**; this worksheet authorizes **internal Arete operator testing only**. Real student/parent/financial records, production payment operations, unsafe test secrets and external authenticated crawling are excluded. Use approved synthetic schools, fixtures, and already-governed test accounts only. CompuWerx payment processing is not authorized.

## Evidence states

- **SOURCE VERIFIED:** accepted code and an identified passing source CI/test record for the exact change; not a deployed runtime pass.
- **HOSTED VERIFIED:** authenticated/synthetic check on a deployed frontend and API with matching exact release SHA, retained sanitized outputs, actual authorization, business effects and negative cases.
- **NOT VERIFIED:** missing, outdated, superseded or mismatched proof. A route, component, UI build, unit test or inventory entry by itself does not imply a verified business journey.
- **BLOCKED:** prerequisite security/recovery/deployment control prevents safe execution. Never replace a required test with a waiver or an all-skipped result.

Record `test/run URL`, immutable source SHA, deployed API build SHA, backend artifact SHA, frontend build SHA, synthetic school/role, test time, status, and sanitized proof pointer for each accepted item. Do not include live credentials, tokens, student PII or unredacted request bodies. Failing tests remain in history; repair and retest rather than rewriting evidence.

## A — Financial aid: application → approval → credit → decline

**Source evidence:** [PR #516](https://github.com/Arete0920/Crown-CSMS/pull/516) fixed director posting; [PR #519](https://github.com/Arete0920/Crown-CSMS/pull/519) merged the reversal repair. Its final PR head had **38 successful and two skipped check-runs, zero failures**; PostgreSQL finance regressions passed **36 tests and two subtests**. Relevant sources: `backend/aid/models.py`, `backend/aid/services/ledger_bridge.py`, `backend/aid/tests/test_option_a_aid_student_accounts_bridge.py`, `backend/crown_api/tests/test_director_aid_posting_integrity.py`. These totals apply to that exact PR head, not automatically to a subsequent release candidate.

**Important frontend limitation:** `frontend/dashboards/src/pages/FinancialAidDashboard.jsx` uses `frontend/dashboards/src/config/dashboardTemplates/financialAidDashboard.js`, which explicitly declares **fallback/template figures**. Its displayed figures are not certified live awards, payments or balances. A source-level ledger correction is **not proof of a working operator decline button**.

| ID | Required acceptance | Current status at this checkpoint |
|---|---|---|
| FA-1 | Authorized internal operator can review a synthetic application/award in the actual routed UI; unauthorized parent/staff requests denied | **NOT VERIFIED as current hosted journey** |
| FA-2 | An approved $250 synthetic award produces exactly one same-school non-cash Credit; no cash Payment; correct legacy ledger and budget; audit persists | **SOURCE VERIFIED for bounded ledger tests; HOSTED OPEN** |
| FA-3 | Declining that award voids the canonical Credit, creates exactly one offsetting legacy reversal, restores budget once, and records immutable audit without cash movement | **SOURCE VERIFIED for bounded ledger tests; HOSTED OPEN** |
| FA-4 | Duplicate/concurrent approval and decline, absent/wrong household, stale award, failed audit or reversal remain idempotent, transactional and tenant-isolated | **SOURCE VERIFIED for bounded PostgreSQL regressions; HOSTED OPEN** |
| FA-5 | UI totals and statements reconcile to canonical database values, without illustrative values passing as live or inactive credits remaining active | **NOT VERIFIED; frontend live-data integration must be established** |
| FA-6 | Full workflow visible on matching-SHA deployed frontend and backend, with sanitized screen evidence and persisted database reconciliation | **NOT VERIFIED** |

**Next action:** First inspect real financial-aid UI actions and their API ownership; implement only a confirmed missing integration with focused frontend/backend tests. Do not fabricate simulated postings or enable a payment gateway. Then run the bounded internal operator workflow under an approved same-SHA synthetic environment.

## B — Platform-owner console: active operator → truthful oversight

**Source evidence:** `frontend/dashboards/src/pages/PlatformOwnerConsole.jsx`, canonical `/master-control`, backend `platform_ops` APIs, `backend/tests/test_platform_operator_authorization.py` and `frontend/dashboards/tests/certification/platform-owner-console.test.jsx`. See [#414](https://github.com/Arete0920/Crown-CSMS/issues/414).

| ID | Required acceptance | Current status |
|---|---|---|
| OWN-1 | Active authorized platform owner opens the canonical deep link and sees live/sanitized school and provisioning summaries on the correct deployed API | **SOURCE IMPLEMENTED; HOSTED OPEN** |
| OWN-2 | School staff, school admins, inactive/school-bound owners and anonymous callers cannot enumerate platform tenants; wrong-role and tenant-header denials are enforced server-side | **SOURCE TESTS EXIST; HOSTED OPEN** |
| OWN-3 | Navigation, pagination and refresh behave correctly under network error/retry; no cross-school or student/family PII is exposed | **FRONTEND SOURCE TESTS EXIST; HOSTED OPEN** |
| OWN-4 | Revenue, payment and unimplemented operating indicators are absent, accurately unavailable, or explicitly labeled; no synthetic totals advertised as real | **SOURCE REVIEW AVAILABLE; HOSTED OPEN** |

**Next action:** Perform an authenticated Arete operator-only DEV walkthrough after the environment/security gates. No buyer accounts, access invitation, corporate-ledger or CompuWerx work is authorized by this checklist.

## C — School provisioning: authorized request → audited activation

**Source evidence:** [PR #421](https://github.com/Arete0920/Crown-CSMS/pull/421), `backend/platform_ops/provisioning.py`, `backend/platform_ops/management/commands/run_school_provisioning.py`, `backend/tests/test_platform_provisioning.py` and `backend/tests/test_platform_operator_authorization.py`. See [#420](https://github.com/Arete0920/Crown-CSMS/issues/420).

| ID | Required acceptance | Current status |
|---|---|---|
| PROV-1 | School creation is an authenticated operator action and queues one synthetic inactive school; duplicate idempotency-key requests do not create duplicates | **SOURCE IMPLEMENTED / TESTS EXIST; HOSTED OPEN** |
| PROV-2 | Approved DEV-only guarded command is tied to an independently authenticated operator, current exact environment/DB identity and logged change approval | **SOURCE IMPLEMENTED / TESTS EXIST; HOSTED OPEN** |
| PROV-3 | Exactly one synthetic job advances queued → succeeded, activates the school only on success, and persists actor, audit and correlation evidence | **SOURCE IMPLEMENTED / TESTS EXIST; HOSTED OPEN** |
| PROV-4 | Concurrent/replayed invocations, failed jobs, audit outages, wrong-role/tenant and retry-policy violations fail closed; rollback and recovery are independently verified | **SOURCE REGRESSIONS EXIST; HOSTED OPEN** |
| PROV-5 | Independent recoverability, migration/TLS state and selected-target backup/restore are verified before any live DEV state change | **BLOCKED on separate controlled [#427](https://github.com/Arete0920/Crown-CSMS/issues/427) evidence** |

**Next action:** Do **not** create a duplicate executor or provision a real school. Host execution requires operator authority, actual recovery evidence, a documented reversible test plan, exact target identity, and independent readback.

## D — Shared release and security gates

| ID | Gate | Source of truth / rule |
|---|---|---|
| REL-1 | Freeze final accepted source and review required terminal checks, including code scanning, repository policy, backend, frontend, API contract, tenant tests and finance PostgreSQL | Protected `main` and [GitHub check runs](https://github.com/Arete0920/Crown-CSMS/actions); no fabricated green or bypass |
| REL-2 | Match selected source, backend build, backend artifact and isolated frontend build identities; assert health and negative anonymous access | [#427](https://github.com/Arete0920/Crown-CSMS/issues/427); same-SHA runtime receipt; current deployment is not accepted by older-source proof |
| REL-3 | Run scoped authenticated six-role/browser and two-synthetic-tenant privacy checks on the deployed candidate, including guardian/household negatives | [#273](https://github.com/Arete0920/Crown-CSMS/issues/273) and [#441](https://github.com/Arete0920/Crown-CSMS/issues/441); historical 51/51 belongs only to source `63121646f6356eadea5e6f2f1bbe02081b2e1491` |
| REL-4 | Prove relevant JWT revocation/refresh, schema and Redis security in selected DEV environment | [#350](https://github.com/Arete0920/Crown-CSMS/issues/350), [#372](https://github.com/Arete0920/Crown-CSMS/issues/372) and [#427](https://github.com/Arete0920/Crown-CSMS/issues/427) |
| REL-5 | Evidence-backed signing-key retirement/distributable acceptance, without erasing incident history | [#104](https://github.com/Arete0920/Crown-CSMS/issues/104) |
| REL-6 | Truthfully distinguish source proof, internal demo, hosted DEV certification, product release, buyer handoff and external audit | `docs/CURRENT_RELEASE_STATUS.md`; written approval remains necessary for each distinct scope |

**Exit rule:** A passing source/build pipeline establishes only the scope it ran. Internal demo approval requires tested source plus matching hosted behavior and explicit owner acceptance. A production customer/payment release or compliance certification requires additional independent gates. Any failed/blocked row remains open and must be carried into the actual diligence disclosure; no unqualified "fully complete" or "certified" claim.

**Retention:** Historical GitHub Releases, tags, incidents and evidence must remain immutable. Deleting an old branch or suppressing a failed run does not resolve a defect. Branch cleanup requires an independent merged/unique-commit and evidence-retention classification.
