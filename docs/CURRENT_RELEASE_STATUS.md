# CROWN Current Release Status

**Successor state (verified 2026-08-11):** `tcmegahan/Crown-CSMS` uses migration baseline `ac574ab2a55ecbfefb40cbd67bad08d99c085575`; no successor production tag or release exists; prior production authority remains historical in preserved `tcmegahan/Crown2026`.

## Current successor release decision

`Crown-CSMS` is the active successor development repository, not a certified production identity; historical `Crown2026` certification does not transfer automatically, and any successor release requires fresh exact-identity certification.

## Prior certified production identity

- Backend source: `ce12c9536ec85346b2446018fa8bfe27edb3ffa0`
- Immutable tag: `prod-deploy-20260808-ce12c95`
- Production Deploy run: `31287503791`
- Dashboard deployment/certification run: `31289219093`
- Dashboard deployment source: `a3f89db677857a220b322b3f1bf094b3fdef3fa2`
- Pre-reconciliation development baseline (PR #1949): `ef9e1fa4f06d6600d60313059f35c0bb564f5a5b`

Production Deploy completed migration authority, exact checkout verification, tests, container build and scan, Azure deployment, deployed build-SHA verification, tenant-aware integrity, health, and end-to-end release identity successfully.

The dashboard run recorded `18/18 PASS`. Fresh verification proved that its assertions did not reject persistent loading, visible summary-service failures, unexpected authorization denial, or an empty required wizard registry. The result remains historical evidence but is not sufficient current owner-handoff certification.

## Previously certified live surfaces

The retained Heritage matrix covered only these exact persona/route combinations:

- `sandbox-admin`: `/`, `/sandbox`, `/sandbox/command-center`, `/admin`, `/school-admin-dashboard`, `/dash/admin`, `/finance`, `/admissions-dashboard`, `/wizards`
- `sandbox-teacher`: `/sandbox`, `/teacher`, `/dash/teacher`
- `sandbox-parent`: `/sandbox`, `/parent`, `/dash/parent`
- `sandbox-student`: `/student`
- `sandbox-board`: `/board`, `/school-board-dashboard`

Auditor was not represented. No universal all-tenant or unsupported-persona certification is claimed.

## Development and identity boundary

Development `main`, the deployed backend, and the deployed dashboard are separate identities. A later commit does not inherit production certification. A current GO requires the exact corrected source, governed deployment, reconciled runtime identities, and fresh certification recorded in `#1619`.

## Payment boundary

External payment processing remains disabled and fail closed. Provider selection, contracting, credentials, transaction certification, settlement, refunds, disputes, and activation are future-owner actions. This remediation does not authorize payment activation.

## Disclosed remaining boundaries

Unless later evidence proves completion, the following remain disclosed: measured rollback and operational-backup restore; exhaustive credential rotation and break-glass exercises; expanded alert and incident exercises; vendor, contractual, regional, and legal reconciliation; full privacy-lifecycle exercises; buyer-controlled account transfer and seller-access removal; and the deferred historical rewrite of the retired key.

## Disposition

Buyer operational turnover: **PENDING IDENTIFIED BUYER AND PARTY ACCEPTANCE**  
**PAYMENT PROCESSING:** DISABLED / FAIL CLOSED / DEFERRED TO NEW OWNER

- Prior bounded production deployment: **HISTORICAL PASS**
- Prior Heritage surface matrix: **18/18 HISTORICAL RESULT; NOT CURRENT HANDOFF PROOF**
- Current buyer diligence package: **NOT READY — SEE #1619**
- Payment processing: **DISABLED / FAIL CLOSED / FUTURE-OWNER ACTION**
- Actual buyer turnover: **PENDING IDENTIFIED BUYER AND PARTY ACCEPTANCE**