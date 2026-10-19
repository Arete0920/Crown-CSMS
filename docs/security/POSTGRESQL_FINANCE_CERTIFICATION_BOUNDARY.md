# PostgreSQL finance hardening evidence boundary

**Scope:** `.github/workflows/finance-final-hardening.yml` and the
`finance-postgresql-hardening` job.

The PostgreSQL job runs the canonical payment, refund, ledger-allocation, and
general-ledger runtime test in an isolated PostgreSQL 16 test database.
`test_option_a_finance_runtime_chain.py` creates a school-bound household,
a tuition obligation, a linked Finance payment and canonical payment, settles
the allocation, and settles a partial refund. It then runs the read-only
`audit_finance_hardening(school_id=school.id)` against those real records.

The test fails if the audit reports an integrity finding **or** fails to examine
payments, Finance allocations, student-account allocations, journal entries,
and their cross-system trace links. A zero-record audit cannot pass.

The legacy `seed_heritage_realism_pack` command invokes
`seed_households.py`, `seed_scheduling.py`, and `seed_finance.py`. These
legacy scripts are intentionally prohibited on PostgreSQL and hosted databases;
they are allowed only in separately authorized, isolated local SQLite fixture
environments. Do not enable them by relabeling PostgreSQL as a local database.

The PostgreSQL test is **source/CI regression evidence**, not proof of any
hosted Heritage state, deployed revision, applied customer migration,
production payment processing, or payment-provider certification. The manual
payment is synthetic; no external gateway is invoked.

To reproduce this precise evidence against an approved disposable PostgreSQL
test database, use the workflow's configured environment and run:

```bash
cd backend
python -m pytest -q payments/tests/test_option_a_finance_runtime_chain.py
```

Rollback is a scoped revert of the workflow and test assertions; never weaken
the tenant/data isolation controls to make a legacy seed run on PostgreSQL.
