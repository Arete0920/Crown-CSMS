# Student Accounts financial fact boundary repair

Status: proposed; requires required CI checks and governed merge.

## Problem and change

Legacy ledger routes accepted authenticated school users without explicit finance grants. All ledger reads now require finance.view, and mutations require finance.edit in the selected school. Positive fixtures receive explicit school grants; negative tests cover authenticated callers without grants.

Charge, Credit and Payment queryset updates, bulk writes and physical deletion now reject operations that bypass instance validation or journal signals. Instance saves validate school/account ownership and existing immutable fields even for forged adding state. Financial fact save and journal signal execution share a transaction so posting failure rolls back the fact. Existing facts are locked during validation on databases that support row locking. Void transitions are irreversible; reactivation would restore balances without corresponding journal posting. No schema migration is introduced.

## Verification and limits

Run ledger, journal, finance and payments suites together, plus combined authorization and tenant regression suites. PostgreSQL locking/concurrency tests must pass on PostgreSQL; SQLite skips are not certification.

These guards protect supported ORM and API writes. They are not database triggers and do not protect raw SQL or private ORM internals. Allocation history, external settlement, provider activation and account identity convergence remain separate work. Existing controlled void/reversal behavior is retained.

## Audit and rollback

Security change: school-scoped finance RBAC replaces authentication-only access. No live credentials, billing provider configuration or production data were changed.

Rollback by reverting this PR under the repository merge policy. A rollback restores the prior weaker API/write boundaries; it is not a credential retirement or ledger reconciliation operation.
