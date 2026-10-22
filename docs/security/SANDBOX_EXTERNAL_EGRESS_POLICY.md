# Heritage sandbox external-communications quarantine

**Release status:** Proposed correction only; not deployed or release-authorized. Issue #273 governs acceptance.

## Invariants

1. The fixed fictional Heritage school is barred from external email, SMS, and Teams delivery, including queued and direct provider paths.
2. The evaluator host MUST set `CROWN_SANDBOX_OUTBOUND_DISABLED=true` on the API **and every worker**. The fixed Heritage school ID is barred even without that setting. Never enable provider traffic for a buyer demo.
3. Suppressed queued messages are terminal DEAD with reason `sandbox_external_egress_suppressed`; never claim sent, retry, or mark delivered. Direct receipts are suppressed.
4. A separate evaluator authorization gate must prohibit buyer business writes; this communications guard does not make any app read-only.
5. No payment processing, email, Teams, SMS, or production credential testing is authorized.

## Release acceptance

- Enumerate all worker processes, outbox routes, direct dispatch paths, provider leaves, and fallback notification channels.
- Test all paths with mocks and assert zero provider calls, including retry, existing queued messages, and recipient/sender combinations.
- Verify unrelated-school dispatch behavior with evaluator mode off, and full host denial with evaluator mode on.
- Verify exact source and deployed SHA, all protected CI/security/tenant tests, Azure settings (without revealing secrets), incident remediation, operational costs, rollback, and session security.
- Do not send a real message to test denial.

**Rollback:** stop evaluator admission and workers first; do not restore an externally reachable deployment without confirmed egress controls.
