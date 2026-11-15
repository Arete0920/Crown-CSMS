# Owned presenter reset with retained history

The reset is an operator command, never an HTTP endpoint or public session.
It builds a new independently scoped fictional school generation from the
Heritage templates and retires the previous owned school/principals. It never
copies old database records, deletes immutable history, truncates shared tables,
rotates existing password hashes or adopts an existing tenant. Original Heritage
and prospect workspaces remain outside the reserved identity namespace.

The root is generation zero. Generations one through four use deterministic
UUID5 identities derived from the reserved root and generation number; each has
its own scoped normal usernames. Five retained schools is a hard capacity limit.
No schedule, automatic storage expansion, cleanup or new recurring resource is
introduced. The owner must verify existing capacity before authorizing hosted
rollover. Reaching the limit refuses another generation; it never erases history.

## Operator sequence

Use the exact local presenter runtime, or a separately owner-enabled exact-SHA
existing DEV runtime described in UNIVERSAL_AZURE_ACTIVATION.md. The owner records
the current school ID and generates one UUID4 request key for this operation:

```sh
CURRENT_PRESENTER_SCHOOL_ID='OWNER_VERIFIED_CURRENT_UUID'
RESET_REQUEST_KEY=$(python -c 'import uuid; print(uuid.uuid4())')
python manage.py reset_universal_presenter \
  --expected-current-school-id "$CURRENT_PRESENTER_SCHOOL_ID" \
  --request-key "$RESET_REQUEST_KEY"
```

Default preflight reads and locks scope without changing records. For hosted
use, also provide `--expected-sha "$EXPECTED_SHA"`; the explicit revision, feature
flag, approved-SHA setting, existing DEV/DB identity and outbound quarantine must
all match. The placeholders intentionally fail until replaced.

After separate owner authorization for hosted provisioning/reset, supply the nine
new-generation secrets through the existing private environment process, then:

```sh
python manage.py reset_universal_presenter \
  --expected-current-school-id "$CURRENT_PRESENTER_SCHOOL_ID" \
  --request-key "$RESET_REQUEST_KEY" \
  --enable-password-login --apply
```

Add the exact `--expected-sha` on hosted DEV. Reuse the same request key for a
transport retry. A committed retry returns ALREADY_APPLIED and cannot create
another generation. A stale current ID, reused key from another/superseded reset,
reserved-ID collision or ambiguous provenance refuses without writes. Capture
the returned new school ID and fictional usernames; use normal login with those
new identities. Existing usernames/password hashes remain unchanged and inactive.
The accompanying frontend source uses a closed list of the five reserved
identities and retains tenant context on every request. Its compiled-browser
acceptance must pass after rollover; never activate a backend-only reset release.

## Atomicity, isolation and custody

The stable root school row serializes every registry/generation decision under
PostgreSQL FOR NO KEY UPDATE. This permits foreign-key KEY SHARE locks from
already-running legitimate transactions while preventing concurrent rollovers.
All expected existing child rows are locked before checking open custody. On
successful retirement, normal model saves deactivate only those owned children
and principals. Admission services waiting for the same active-child row must
recheck that predicate after the transaction commits. If an admission already
holds the child lock, the reset waits and then refuses its unresolved custody.
Existing custody safety/model validation is preserved; no bulk childcare update
or delete bypass is used.

Open Daycare, AM/PM or Camp custody blocks retirement. Complete authorized pickup,
handoff or supervisor reconciliation first. Foreign/unscoped principal role
associations, cross-school principal/child relationships, unexpected account
inventory and privileged principals also block retirement. New fixture failure
rolls back both retirement and every new school/module record in one transaction.

All old financial/SGO applications, budgets, ledger and audit records, custody
history, immutable academic revisions and principal IDs are retained. No global
role grants change. Every reserved generation is unconditionally quarantined from
external communication, including role-only memberships, even if the host-wide
outbound flag is accidentally absent. New-generation Jireh grants and ordinary
roles are independent; prior identities cannot authenticate to the new school.

## Acceptance and limits

Local acceptance repeats actual Aid submission after two successive generations,
verifies old records/password hashes/global grants remain, rejects old normal
login, tests stale/repeated requests, refuses custody/foreign roles/collisions,
and injects a partial fixture failure to prove rollback. PostgreSQL admission
versus reset tests exercise both lock orderings using the real database and care
service; only the unrelated cloud runtime predicate is mocked in CI/local tests.
This does not certify a deployed Azure runtime or override owner release gates.

Bootstrap destructive reset remains limited to the initial unprotected foundation;
it refuses retained generations. Academic archive is still a smaller repeat
operation that preserves history and normal identity. Camp ordinary full
forms/health clearance, initial parent admissions/signatures and full finance
acceptance remain unsupported/unverified as described in the current readiness
ledger. A new generation does not fabricate those missing product workflows.

No live provisioning/reset was executed for this assignment. A source rollback
alone cannot reactivate retired principals or safely erase a generation. Keep
audit evidence and use the existing owner-authorized containment/recovery process
for any correction; never repair the presenter by changing another school.
