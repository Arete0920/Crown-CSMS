# CROWN Current Release Status

Date: 2026-07-15
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
- Visibility: private
- Default branch: `main`
- Current main SHA observed through the GitHub connector on 2026-07-15: `6a8492e874d9fee26cbc848e2a74b94d0946c3c7`
- Latest main change: PR #1349, a documentation-only architecture-authority change with no runtime, workflow, deployment, security-control, or ownership change.
- PR #1349 integration checks completed successfully before merge; this does not by itself prove post-merge current-main or deployed-runtime settlement.
- Current-main same-SHA required-gate settlement: **NOT PROVEN by this document**.
- Production deployment SHA alignment with current main: **NOT PROVEN by this document**.
- Open PR and issue state must be checked live; counts in historical evidence packets are not current authority.

## Active Release-Critical Work

### Dashboard plumbing and data provenance

- #1274 — authenticated dashboard live-data proof for school administrator, teacher, and parent.
- #1287 — live tenant-context propagation and `X-School-Id` or trusted authenticated-school-context proof.
- Snapshot, sample, fallback, scaffold, hybrid, or unknown data must not be certified as live without current authenticated evidence.

### Recovery and deployment operations

- #1270 — automated rollback behavior, controlled rollback drill, restore evidence, and recovery decision tree.
- Deployment success or runtime health alone is insufficient without proven recovery and restoration capability.

### Security and secrets

- #1294 — production secrets management and external Vault or Azure Key Vault readiness.
- #1296 — rotation, audit, and break-glass runbook.
- Repository scanning and guardrails do not independently prove external production secret-store configuration or operational rotation.

### Payment-provider readiness

- #1298 — tenant-selected provider readiness for Stripe, CompuWerx naming pending vendor normalization, and Metro Merchant Services.
- No provider may be represented as production-enabled for a school until contracts, credentials, webhook behavior, settlement and refund controls, tenant isolation, and security obligations are verified.

### Visual and release-visible QA

- #1276 — complete release-visible route sweep with current browser, network, console, role, and tenant-context evidence.

### Release authority and handoff

- #1275 — final release-authority reconciliation after evidence blockers close.
- #1277 — release notes, changelog, and production-runbook posture.
- #1343 — repository stabilization, provenance, ownership-transfer, and cost-containment program.
- #1337 — systemic CI and certification architecture review.

## Product Completion Evidence

Historical completion evidence remains useful for product-surface coverage, but it does not independently authorize production.

| Area | Repository evidence posture | Release meaning |
| --- | --- | --- |
| Modules | 51 / 51 previously recorded as proven for product-scope coverage | Historical product-scope evidence only |
| Dashboards | 40 / 40 previously recorded for internal surface coverage | Current authenticated live-data provenance still requires closure |
| Wizards | Previously certified for historical scope | Does not authorize production |
| Components and widgets | Previously covered through parent-surface evidence | Does not authorize production |
| Controlled sandbox | Candidate | Requires current same-SHA runtime proof and owner authorization |
| Production | NOT APPROVED | Blocked by current evidence and operational work |

## Required Production Entry Gates

Production authorization requires all of the following on one current release SHA:

1. Required GitHub checks settled with pending=0, failed=0, cancelled=0.
2. Current deployed frontend and backend build identities proven equal to the approved release SHA or explicitly approved compatible SHAs.
3. Authenticated school-administrator, teacher, and parent browser flows proven.
4. Tenant context proven across login, navigation, dashboard API calls, and data access.
5. Dashboard provenance proves live authenticated API data; sample, snapshot, fallback, scaffold, hybrid, and unknown classifications do not pass as live.
6. Automated rollback behavior corrected and a rollback or failed-deploy simulation completed.
7. Restore or equivalent recovery evidence completed with accepted RTO and RPO.
8. Current secret scan, external secret-store configuration evidence, rotation policy, audit evidence, and break-glass process completed.
9. Payment-provider production boundary resolved without unsupported activation claims.
10. Release-visible visual QA completed with no unexplained console or network failures.
11. Release notes, changelog, deployment runbook, ownership-access register, and final authority record updated.
12. A successor or designated reviewer completes clean-clone setup, test, operation, deployment, and recovery validation.
13. Explicit Founder/Product Owner production authorization recorded after all preceding gates pass.

## Allowed Language

Allowed:

- "CROWN is in controlled sandbox release-candidate posture."
- "CROWN has substantial product-surface completion evidence."
- "Production release is not approved."
- "Current production readiness depends on authenticated tenant-scoped live-data proof, operational recovery, external secrets controls, payment activation controls, visual QA, same-SHA settlement, and transfer validation."

Not allowed:

- forbidden claim: "CROWN is unrestricted production ready."
- "CROWN is production GO."
- "All dashboards are live" when current evidence includes snapshot, sample, fallback, scaffold, hybrid, or unknown data.
- "Independent review is complete" unless independently evidenced and documented.
- "Ownership transfer is complete" unless repository, infrastructure, external services, credentials, contracts, recovery access, and successor validation are documented.
- "An open or unmerged PR is shipped authority."

## Current Final Status

**CONTROLLED SANDBOX CANDIDATE / PRODUCTION NOT APPROVED**.
