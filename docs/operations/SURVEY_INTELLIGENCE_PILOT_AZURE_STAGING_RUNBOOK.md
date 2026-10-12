# Survey Intelligence — Pilot and Azure Staging Acceptance Runbook

**Status:** Pre-deployment operating plan. Pilot, Azure tenant, staging runtime, migration and live deployment are NOT VERIFIED.
**Tracking:** Issue #204 SI-P04 and SI-P05.
**Source authority:** CROWN School Implementation Runbook, Current Release Status, security and architecture canons.

## Pilot charter

- Proposed cohort: one authorized school tenant (Heritage synthetic demonstration first; separate consenting real-school adult pilot later).
- Pilot sponsor: school head or delegated administrator, recorded at intake.
- Operational owner: CROWN implementation lead; designated backup and incident contact.
- Initial instruments: original adult Parent Experience, Post-Tour Feedback and Re-enrollment Intent drafts. No student/child surveys.
- Success criterion: an authorized school admin creates, approves, publishes, closes and reports a correctly versioned adult survey; a genuine consenting adult can respond without exposure of identity; follow-up leadership action is recorded and reviewed.
- Research caveat: 10+ valid submissions only allows provisional aggregate display under proposed suppression limits, **not** statistical representativeness or benchmark validity.
- Stop conditions: a cross-school disclosure, invalid published-question modification, direct child audience, missing consent/notice where required, log-based reidentification, uncontrolled token reuse, forbidden access, failed deletion behavior, missing audit trail or critical/high severity finding.

### Step-by-step pilot acceptance

1. **School authorization:** record sponsor signature, pilot dates, audience, contract/school policy and data protection approval. Do not presume a Heritage demo institution is consenting to production research.
2. **Instrument freeze:** review wording, source provenance, protected-category screening and adult comprehensibility; preserve signer, dated version, SHA and approved notice.
3. **Controlled synthetic rehearsal:** two isolated school tenants; adult test users; no real family, student or finance data; cross-school and role denial proofs.
4. **API/UX verification:** execute ADM/PUB/RSP/REP/ACT cases from the separate acceptance standard, including mobile and assistive technology.
5. **Threat and privacy audit:** verify token expiration/revocation, no pseudonymous linkage in response or logs, duplicate rejection, small sample inference, export restrictions and error resilience.
6. **Report review:** confirm denominators, nonresponses, suppression and explicit limitations; hide nonreportable findings; never show demo data as live.
7. **Leadership action:** record one real improvement objective with a responsible adult owner and a next review date. Do not claim operational impact from sample answers.
8. **Evidence archive:** retain exact SHA, test artifacts, school scope, approver, exceptions and release authorization; permit rollback.
9. **Pilot decision:** named school sponsor and product/release owner record GO/NO-GO only on actual evidence.
10. **Expansion decision:** confidential, identifiable, child-facing, benchmarking, individual forecasting and cross-school use remain excluded until separately authorized and certified.

## Azure staging preparation checklist

### Configuration and least privilege
- [ ] Confirm Azure subscription **Active**, correct tenant/subscription and permitted region, resource group and cost/budget caps. Account status in screenshots is not staging-runtime evidence.
- [ ] Resolve actual compute/database/cache/secret provider/storage choices within existing approved cost constraints. No new paid subscriptions or automatic infrastructure purchase assumed.
- [ ] Establish staging DNS/HTTPS, trusted origin and verified build SHA; restrict administrative routes; no production student/financial PII in staging.
- [ ] Configure managed identity or least-privilege service principal, environment-specific secrets and rotation; never commit credentials.
- [ ] Ensure school identity, JWT/session, canonical tenant header and RBAC are enforced in staging.
- [ ] Verify secure connection to persistent DB and migration permissions without cross-environment data reuse.

### Application hardening
- [ ] Execute clean install and dependency lock/audit checks on exact head.
- [ ] Run Django system check, planned migration output and historical-schema reconciliation.
- [ ] Rehearse migrations on disposable database; retain migration hash and result.
- [ ] Verify dataset backup and restore with actual recovery measurements, not a mere backup-enabled toggle.
- [ ] Demonstrate safe startup, readiness/liveness, HTTPS and logging redaction; prevent raw anonymous submission in proxy/CDN/app telemetry.
- [ ] Verify shared rate-limit store availability and fail-closed behavior; exercise token expiry/revocation and retries.
- [ ] Test survey publication immutability, school isolation, action RBAC, consent enforcement and denied direct URLs.
- [ ] Verify monitoring/alerting, owner inquiry notification, audit retention and incident escalation.
- [ ] Execute rollback/redeployment to known-good exact SHA; verify database forward/backward compatibility.
- [ ] Record per-environment operational cost budget and daily run estimate using real pricing, no invented free-tier assertions.

### Release evidence fields

| Evidence | Required recorded value |
| --- | --- |
| Subscription/tenant/resource group and region | NOT VERIFIED |
| Staging app URL, TLS/DNS identity | NOT VERIFIED |
| Git commit SHA / image digest | NOT VERIFIED |
| Datastore/secret/backup resource IDs | NOT VERIFIED |
| Migration run and validation log | NOT VERIFIED |
| School-specific test tenancy and sanitized fixture | NOT VERIFIED |
| 2-tenant / RBAC / child-access-negative evidence | NOT VERIFIED |
| Approved notice, privacy/legal/IP review | NOT VERIFIED |
| Mobile and accessibility evidence | NOT VERIFIED |
| Recovery drill (RTO/RPO measured) | NOT VERIFIED |
| Monitoring, alert and incident exercise | NOT VERIFIED |
| Approval and release decision | NOT VERIFIED |

**GO/NO-GO:** Missing any release-critical item means that capability is **NOT VERIFIED**, not automatically GO. Source CI passing does not establish operational deployment acceptance. This runbook never authorizes payment activation or changes to production release status.

## Pilot closure criteria

Pilot can close only when the school sponsor has accepted its workflow and reports, security/privacy/IP reviews are recorded, test evidence corresponds to exact deployment SHA and at least one school improvement action has owner and review timing. A planning document or demonstration screenshot alone cannot close the pilot.
