# Parent data-rights request intake

Status: source intake control; school fulfillment and deployed operation require separate verification.
Decision owner: TC Megahan, with the school's designated privacy contact for fulfillment.

## Receipt contract

Authenticated POST requests to `/api/compliance/parent-rights/` and
`/api/v1/compliance/parent-rights/` accept `request_type` values
`export`, `correction`, or `deletion`. The canonical school resolver
validates school context and authorized tenant selection before any receipt is
written. Request bodies cannot select the actor, school, consent type or outcome.

A durable `ConsentAudit` row records the distinct `data_rights_request` event,
the authenticated requester, canonical school and request type, with
`metadata.status=received`. The existing audit store is reused; this event
is explicitly not privacy acceptance, school authorization or parental consent.
The receipt timestamp uses the existing `accepted_at` column as its storage
timestamp, not as evidence of legal consent. No IP address or student record is
required for this intake.

Only after persistence succeeds does the API return HTTP 202 with
`status=received`, `request_type` and the audit row's `request_id`.
The browser serializes JSON, checks the receipt and prevents overlapping clicks.
A timeout can still occur after a successful write: the UI directs the requester
to contact the school before retrying. No cross-session idempotency is claimed.

## School handling and activation boundary

This endpoint records intake only. It does not export student records, grant
guardian access, correct or delete records, send notifications, or provide an
automated staff work queue. Do not activate this intake for live schools until
the school assigns a privacy contact and verifies a restricted receipt-review
and fulfillment procedure, including:

1. Review pending `data_rights_request` events for the selected school using
   authorized restricted access. Do not expose the cross-school audit store to
   parents or ordinary staff.
2. Verify the requester and guardian/student relationship through school records;
   authentication alone does not establish rights to a particular student's data.
3. Apply applicable school policies, legal holds, retention requirements,
   contractual obligations and qualified legal review where needed.
4. Fulfill approved requests through authorized, school-scoped workflows and
   protected delivery; record the decision, reviewer, dates and fulfillment
   evidence in the school's restricted tracking system.
5. Reconcile backup/deletion obligations, exceptions and response deadlines.
   An intake receipt is not evidence that a request has been fulfilled.

The release owner must verify those steps in the intended environment before
claiming a complete parent-rights workflow. This source change grants no
production deployment, legal approval or compliance certification.

## Historical event reconciliation

Earlier code recorded rights requests as `parental_consent` with a
`metadata.request_type` value, sometimes under tenant `unknown`.
Those events must not be relied upon as consent. A qualified, authorized
reviewer should inventory these historical rows in restricted storage, trace
their original requester and school using reliable evidence, and disposition
them with a preserved audit trail. Do not guess school identity or bulk relabel
historical records automatically. This migration changes event choices only
and deliberately preserves original records.

## Verification and rollback

Backend regression tests cover durable receipts, both route aliases,
unauthenticated requests, missing/invalid/inactive school context, unauthorized
cross-school selection (including ordinary staff), spoofed payloads, malformed
requests and storage failure. Frontend tests cover all three JSON submissions,
pending feedback, overlapping clicks, failures and malformed receipts.

Rollback: revert the source change through the governed release process.
Preserve received event rows and do not relabel them as consent. Reverting the
choices migration does not authorize deleting historical audit evidence.
