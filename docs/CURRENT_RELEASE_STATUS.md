# CROWN Current Release Status

**Last reconciled:** 2026-08-09  
**Repository:** `tcmegahan/Crown2026`  
**Controlling authority:** GitHub issue `#1619`  
**Certified release source:** `ce12c9536ec85346b2446018fa8bfe27edb3ffa0`  
**Immutable production tag:** `prod-deploy-20260808-ce12c95`  
**Production deployment run:** `31287503791`

## Certified production identity

- Backend source: `ce12c9536ec85346b2446018fa8bfe27edb3ffa0`
- Immutable tag: `prod-deploy-20260808-ce12c95`
- Production Deploy run: `31287503791`
- Dashboard deployment/certification run: `31289219093`
- Dashboard deployment source: `a3f89db677857a220b322b3f1bf094b3fdef3fa2`
- Pre-reconciliation development baseline (PR #1949): `ef9e1fa4f06d6600d60313059f35c0bb564f5a5b`

Production Deploy completed migration authority, exact checkout verification, tests, container build and scan, Azure deployment, deployed build-SHA verification, tenant-aware integrity, health, and end-to-end release identity successfully.

The dashboard run built and deployed the dashboard, validated the exact backend identity, created the passwordless Heritage session, and completed the retained live-certification matrix with `18/18 PASS`, `0 FAIL`, zero failed network observations, zero console errors, zero missing or non-live provenance observations, and zero critical/serious accessibility violations.

## Certified live surfaces

The retained Heritage matrix certifies only these exact persona/route combinations:

- `sandbox-admin`: `/`, `/sandbox`, `/sandbox/command-center`, `/admin`, `/school-admin-dashboard`, `/dash/admin`, `/finance`, `/admissions-dashboard`, `/wizards`
- `sandbox-teacher`: `/sandbox`, `/teacher`, `/dash/teacher`
- `sandbox-parent`: `/sandbox`, `/parent`, `/dash/parent`
- `sandbox-student`: `/student`
- `sandbox-board`: `/board`, `/school-board-dashboard`

Auditor is not represented in this matrix. No universal all-tenant or unsupported-persona certification is claimed.

## Development boundary

Current `main` followed the certified backend source and dashboard deployment source with bounded deployment-observer and cleanup work. It is not itself the deployed backend or dashboard identity and must not be represented as automatically production certified.

## Payment boundary

External payment processing remains disabled and fail closed. Provider selection, contracting, credentials, transaction certification, settlement, refunds, disputes, and activation are future-owner actions.

## Disclosed remaining boundaries

Unless later evidence proves completion, the following remain disclosed: measured rollback and operational-backup restore; exhaustive credential rotation and break-glass exercises; expanded alert and incident exercises; vendor, contractual, regional, and legal reconciliation; full privacy-lifecycle exercises; buyer-controlled account transfer and seller-access removal; and the deferred historical rewrite of the retired key.

## Disposition

Certified repository release technical gates: **PASS**  
Certified production deployment and runtime technical gates: **PASS**  
Founder/Product Owner release authorization for the certified release: **RECORDED / ACCEPTED**  
Buyer operational turnover: **PENDING IDENTIFIED BUYER AND PARTY ACCEPTANCE**  
**PAYMENT PROCESSING:** DISABLED / FAIL CLOSED / DEFERRED TO NEW OWNER

- Repository and production technical certification for the bounded release: **PASS / COMPLETE**
- Live Heritage surface certification: **18/18 PASS / COMPLETE**
- Payment processing: **DISABLED / FAIL CLOSED / FUTURE-OWNER ACTION**
- Buyer diligence package: **READY AFTER CANONICAL RECORD RECONCILIATION**
- Actual buyer turnover: **PENDING IDENTIFIED BUYER AND PARTY ACCEPTANCE**
