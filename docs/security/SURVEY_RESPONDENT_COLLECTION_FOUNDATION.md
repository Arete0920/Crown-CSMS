# Survey respondent collection foundation — issue #204

## Bounded change and authority

Base inspected: `2684f27acfe51a38feb3cc38ee8a4bc436ea9c03`.
Outcome: internal adult anonymous one-use respondent grants, publication-bound
persistence and neutral retry receipts. Owner: John C. Megahan, under the explicit
issue #204 implementation instruction and approved solo-maintainer governance
path. Automated checks and source inspection are not independent human approval
or approval authority. Public routes, invitations, frontend, deployment,
dependencies and existing gates are outside this change.

One canonical survey domain remains authoritative. Existing publication,
validation and internal persistence services are reused. The legacy UUID
`public_token` is not respondent authority and is not accepted by the new service.

## Internal contract

- `issue_respondent_grant` requires an active school, active authenticated user
  with school-scoped `survey.edit`, active anonymous survey, an intact latest
  publication and aware future expiry no more than 30 days away. The publication
  id and fingerprint are fixed at issuance. Issuance never enables collection.
- The bearer secret is generated with 256 bits of randomness, returned once,
  and stored only as an HMAC digest. No school, family, student or application
  identity is recorded for the respondent. Grant issuer identity is staff audit
  provenance, not respondent identity.
- `collect_response` accepts bytes of at most 64 KiB and exactly `answers`,
  `notice_sha256` and `retry_key`. Duplicate JSON keys, nonfinite JSON numbers,
  identity/scope/metadata injection, invalid typed answers and more than 40
  answers are rejected. The notice acknowledgement binds the full immutable
  publication fingerprint (including notice and questions), not just notice text.
- Collection independently requires active school, active anonymous survey,
  `public_enabled`, unexpired survey collection and grant, and no revocation.
  No service here turns `public_enabled` on. The latest publication must still
  be the grant publication; newer publications invalidate old authority.
- A persisted per-grant budget permits at most 30 lifetime well-formed attempts,
  including failed notice/answer checks and retries. It is an internal bounded
  abuse safeguard, not a public network rate-limit policy. Database failures
  fail closed. Invalid secret/body shapes are rejected before database work.
- Collection serializes on the grant, then school and survey; response and
  receipt persist in one transaction. Unique one-to-one receipt constraints
  prevent a second accepted response even with a different retry key. An exact
  canonical answer payload and same bounded opaque retry key returns the same
  random receipt. Changed payload/key conflicts. Closed/revoked/expired authority
  cannot retrieve a receipt through replay.
- Only keyed retry and payload digests are retained with receipts. No raw bearer
  secrets/retry keys, IP, user agent or arbitrary metadata are logged or stored.
  Respondent result is only a receipt UUID, never response/tenant/grant objects.
  Grant/receipt rows have no new API/export/admin exposure.
- SQLite writer contention can fail closed; retry may subsequently succeed.
  PostgreSQL row/write locks serialize successful competing submissions.

## Privacy and acceptance limits

A random grant-to-response receipt relation supports one-use enforcement. Its
access and retention must be restricted: distributors who associate tokens with
people could compromise anonymity. Do not retain token/identity distribution
maps or describe the design as unlinkable to a party that knows distributed
secrets. Anonymous grants do not prove one unique eligible person per response.
Free-text answers can contain self-identifying information; notices, instrument
review, restricted raw-answer access and reporting suppression remain required.

Separate school approval, legal/privacy/IP review, approved adult respondent
notice and distribution policy, retention/deletion (including grant/receipt
records), credential rotation, public network/global abuse controls, CSRF/origin
and edge body limits, safe telemetry, browser journeys, deployment/migration/
restore rehearsal and operational acceptance remain NOT VERIFIED. No invitations,
public endpoint, school pilot, child collection or production readiness is
accepted by this source change. New grants do not constitute those approvals.
Changing the application SECRET_KEY invalidates outstanding HMAC authority and
retry matching; planned credential/retention operations must account for this.

## Verification and rollback

Run focused survey regressions including tenant denial, expiry/revocation/closure,
publication changes, replay, malformed data, transaction rollback, disclosure and
real concurrent collectors; migration drift checks; then exact-head governed CI.
Resolve every actionable finding and review thread, verify ancestry/mergeability,
and merge with expected-head protection using the existing solo-maintainer path.

Rollback: disable collection, revoke outstanding grants, revert the bounded source
commit. Preserve response/receipt evidence; do not reverse the additive migration
on a database containing grants/receipts until retention and recovery disposition
is authorized. This document does not claim executed runtime rollback.

## Durable transaction and PostgreSQL verification continuation

Continuation base: `fa348da89a95b0fe4ec79e807a33bba73bf0e6ad`.
Bounded outcome: make the attempt budget durable under supported callers and
prove concurrency with a real PostgreSQL service in isolated CI. Owner and
approved solo-maintainer governance remain as above. No public route, deployment,
invitation, schema change or new application dependency belongs to this change.

A reproduced caller-boundary gap allowed an enclosing transaction to roll back
attempt counters along with failed submissions. Collection now requires database
autocommit and rejects enclosing atomic/manual transactions before writing.
Future callers using `ATOMIC_REQUESTS` must use an explicitly reviewed non-atomic
entry boundary and must not wrap collection in a larger transaction. This is an
internal contract requirement, not approval for an HTTP route. Response/receipt
persistence still uses the service-owned atomic transaction.

The dedicated `survey-postgresql` job in the existing Tests workflow uses the
existing PostgreSQL 16 CI service pattern and pinned actions/dependencies. A
fail-closed scope job requires it for relevant survey/core/settings/test and
workflow changes (or unknown ancestry/manual runs); unrelated changes can skip
this added job without changing existing full backend gates. No new top-level
workflow or canonical-inventory exception is introduced. It explicitly requires
PostgreSQL rather than accepting a fallback database. It runs the survey contract
suite, strict identical/conflicting concurrent submissions, simultaneous final
budget attempts, and both commit orderings for revocation/closure. Tests observe
actual PostgreSQL lock waits with bounded timeouts and preserve JUnit evidence.
SQLite runs retain their fail-closed busy-writer behavior and cannot substitute
for these PostgreSQL tests. Exact grant/survey expiration boundaries are also
covered. CI database proof is separate from Azure/runtime deployment, real-school
approvals, retention/distribution policy and operational restore acceptance.

Rollback: revert this bounded service/test/workflow/documentation change; there
is no new schema or data conversion. Retain the established collection-disabled
and separate public acceptance gates. Record final exact-head workflow results
and inspection findings on the controlling PR and issue #204 before acceptance.
