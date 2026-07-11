# CROWN Current Release Status

Date: 2026-07-11
Purpose: Canonical repository-level release posture for CROWN.

## Canonical Authority

1. This file is the repository-level release authority.
2. Current controlling posture is **CONTROLLED SANDBOX CANDIDATE / PRODUCTION NOT APPROVED**.
3. Historical GO, SHIP, PASS, RELEASE_READY, PARTIAL, prior candidate-SHA documents, local transcript notes, and superseded audit packets are non-authoritative unless this file explicitly promotes them.
4. Product, sandbox, pilot, and production claims require current repository evidence and same-SHA gate settlement.
5. This file does not approve unrestricted production release.

## Current Decision

- Repository-wide decision: **SANDBOX_RELEASE_CANDIDATE**.
- Production release decision: **NOT APPROVED**.
- Current controlling posture: **CONTROLLED SANDBOX ONLY; LIVE PROOF AND OPERATIONAL BLOCKERS REMAIN OPEN**.

## Current Repository Snapshot

- Repository: `tcmegahan/Crown2026`
- Default branch: `main`
- Current main SHA observed through the GitHub connector on 2026-07-11: `7bf185e5f65ec4bf2b765d6edb485d06ea7096b3`
- Latest main change: PR #1302, a two-line ESLint-comment cleanup with no runtime, backend, or release-authority change.
- Current-main same-SHA required-gate settlement: **NOT PROVEN by the connector snapshot**.
- Production deployment SHA alignment with current main: **NOT PROVEN by this document**.
- Open PR state and open issue state must be checked live; counts in historical evidence packets are not current authority.

## Active Release-Critical Work

### Dashboard plumbing and data provenance

- #1281 — controlling blocker burn-down lane.
- #1274 — authenticated dashboard live-data proof for school administrator, teacher, and parent.
- #1287 — production tenant-context propagation and `X-School-Id` proof.
- #1289 / PR #1285 — no-pretend provenance and snapshot-versus-live certification.

PR #1285 is draft-only until it is synchronized with current main and its required checks settle with pending=0, failed=0, cancelled=0. Snapshot, sample, fallback, or unknown data must not be certified as live.

### Recovery and deployment operations

- #1270 — automated rollback, controlled rollback drill, restore evidence, and recovery decision tree.
- Deployment success alone is insufficient without proven recovery and restoration capability.

### Security and secrets

- #1294 — production secrets management and Vault readiness.
- #1295 / PR #1301 — repository secret-scanning and ignore guardrails.
- #1296 — rotation, audit, and break-glass runbook.

Ignore rules are preventive controls only. They do not prove that the repository or deployment environment is secret-clean.

### Payment-provider readiness

- #1298 — provider-agnostic readiness for Stripe, CompuWerx, and Metro Merchant Services.
- No provider may be represented as production-enabled until contracts, credentials, webhook behavior, settlement/refund controls, tenant isolation, and security obligations are verified.

### Visual and release-visible QA

- #1272 / PR #1300 — Microsoft asset integrity on `/board`.
- #1276 — complete release-visible route sweep with browser, network, and console evidence.
- PR #1279 remains draft until synchronized with current main and locally validated.

## Product Completion Evidence

Historical completion evidence remains useful for product-surface coverage, but it does not independently authorize production.

| Area | Repository evidence posture | Release meaning |
| --- | --- | --- |
| Modules | 51 / 51 previously recorded as PROVEN | Product-scope evidence only |
| Dashboards | 40 / 40 previously certified for internal scope | Live authenticated provenance still requires closure |
| Wizards | Previously certified | Does not authorize production |
| Components and widgets | Previously certified by parent-surface coverage | Does not authorize production |
| Controlled sandbox | Candidate | Requires current live proof refresh and owner authorization |
| Production | NOT APPROVED | Blocked by current P0 evidence and operational work |

## Required Production Entry Gates

Production authorization requires all of the following on one current release SHA:

1. Required GitHub checks settled with pending=0, failed=0, cancelled=0.
2. Current deployed build SHA proven equal to the approved release SHA.
3. Authenticated school-administrator, teacher, and parent browser flows proven.
4. Tenant context proven across login, navigation, dashboard API calls, and data access.
5. Dashboard provenance proves live authenticated API data; sample, snapshot, fallback, and unknown classifications do not pass.
6. Automated rollback and restore/recovery evidence completed.
7. Current secret scan, Key Vault configuration evidence, rotation policy, and break-glass process completed.
8. Payment-provider production boundary resolved without unsupported activation claims.
9. Release-visible visual QA completed with no unexplained console or network failures.
10. Release notes, changelog, deployment runbook, and final authority record updated.
11. Explicit Founder/Product Owner production authorization recorded after all preceding gates pass.

## Allowed Language

Allowed:

- "CROWN is in controlled sandbox release-candidate posture."
- "CROWN has substantial product-surface completion evidence."
- "Production release is not approved."
- "Current production readiness depends on authenticated tenant-scoped live-data proof, operational recovery, secrets controls, visual QA, and same-SHA gate settlement."

Not allowed:

- "CROWN is unrestricted production ready."
- "CROWN is production GO."
- "All dashboards are live" when evidence includes snapshot, sample, fallback, or unknown data.
- "Independent review is complete" unless independently evidenced and documented.
- "An open or unmerged PR is shipped authority."

## Current Final Status

**CONTROLLED SANDBOX CANDIDATE / PRODUCTION NOT APPROVED**.
