# Repository repair — September 30, 2026

Audit baseline: `ee441bdf22c59eb44499d0ca2878eaa2e968ea1e`.

## Findings and corrections

- Main has six failing workflows: Dependency Scan, Dependency Audit, Tests, Wizard E2E Evidence Gate, Finance Final Hardening, and Exact Main Backend Coverage.
- The two dependency workflows identify PyJWT and frontend transitive vulnerabilities. Reuse the exact PyJWT 2.14.0, brace-expansion 5.0.12, undici 7.29.1 and lockfile repairs already verified on PR #40. Once this repair lands, those existing PR changes should disappear from its main-relative diff.
- Full backend evidence reports 18 failures and one teardown error. Fixtures contain duplicate blank email identities, retired aftercare integer identifiers, outdated response keys, missing persistent permissions, and expected delete exceptions that poison the enclosing transaction. Replace these assumptions with canonical identities, real grants, current response contracts and transaction savepoints. Restricted metrics remain denied without the restricted grant.
- The central DRF permission fallback resolves a school but does not propagate it to downstream permission checks. Propagate the verified school context; retain persistent RBAC enforcement.
- Wizard evidence passes 55 of 56 transactions; the remaining assertion expects the retired Section Scheduler heading. Assert the current Kairos heading while retaining all live placement/persistence and unauthorized-user checks.
- Finance whitespace evidence identifies excess EOF blank lines in two CrownPass documents. Remove those lines.
- Governed coverage is 78.198340%, above the unchanged 75% requirement. Its baseline workflow fails because the authoritative test suite fails, not because the coverage percentage is below threshold.
- Full backend tests, wizard browser transactions and governed coverage currently run only after merge or manual dispatch. Add path-scoped pull-request triggers so these failures are exposed before merge; preserve their existing execution, evidence and fail-closed behavior.

## Separate operational blocker

Azure Drift Watchdog repeatedly fails before any infrastructure assertion: no Azure authentication is configured. No Azure invariant is verified by those failed runs. The owner instructed cancellation of automatic Azure checks on September 30, 2026. Remove the watchdog schedule; retain manual dispatch for a future explicit operator request. No Azure run was queued or active when cancellation was requested. Azure infrastructure remains unverified. Any later reactivation requires configured authentication and a complete successful manual dispatch; cancellation does not establish production readiness.

## Verification and authority

Local Python and frontend vulnerability audits report no known vulnerabilities. Frontend lint and production build pass. Backend and browser evidence must be evaluated on the repair PR's exact head before merge. No repository hygiene limit, coverage threshold, required scan, payment activation rule, or production-release authority is relaxed. No production readiness is claimed.

SOLO_DEVELOPER_APPROVED_WORKAROUND

Audit note: this repair changes central tenant-context propagation and adds pre-merge gates. Automated assistance is not approval authority. Merge remains conditional on exact-head checks and the approved solo-maintainer controls.
