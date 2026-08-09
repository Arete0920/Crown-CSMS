# CROWN Release Notes

## Certified bounded production release — 2026-08-08

- **Source:** `ce12c9536ec85346b2446018fa8bfe27edb3ffa0`
- **Immutable tag:** `prod-deploy-20260808-ce12c95`
- **Production deployment run:** `31287503791`
- **Dashboard deployment/certification run:** `31289219093`
- **Dashboard deployment source:** `a3f89db677857a220b322b3f1bf094b3fdef3fa2`
- **Authority:** GitHub issue #1619
- **Status:** Certified and deployed

### Verified release scope

- exact-source migration authority, tests, container build and scan, Azure deployment, deployed build-SHA verification, tenant-aware integrity, health, and end-to-end release identity;
- retained live dashboard certification: `18/18 PASS`, `0 FAIL`, zero failed network observations, zero console errors, zero missing or non-live provenance observations, and zero critical/serious accessibility violations;
- certified Heritage surfaces for sandbox admin, teacher, parent, student, and board personas only;
- external payment processing disabled and fail closed.

Auditor is not represented in the retained live matrix. No universal all-tenant or unsupported-persona certification is claimed.

### Deferred and transaction-specific boundaries

External payment processing remains disabled and deferred to a new owner. Buyer-specific accounts, credential transfer, seller-access removal, contracts, legal acceptance, and payment-provider activation remain pending an identified buyer.

Residual operational maturity work is disclosed in `docs/KNOWN_LIMITATIONS.md` and #1619.

## Post-release change control

Later commits on `main` do not redefine the certified backend or dashboard identity unless separately authorized, deployed, and certified. Each post-release repair must identify its exact head, tests, review status, and runtime-proof requirements.

## Historical releases

### `crown-0.3.1-prod-pipeline-fix` — 2026-01-27

Historical pipeline milestone at `a1c4c42a381e03587c784bd995ec8fd6c33aeee9`. It is not the current certified production identity.

### `crown-0.3.0-spine-complete` — 2026-01-27

Historical tenant-isolation and CI foundation at `340c7e3fbb882eb4886fbfbbe8e648f3866e5178`. It is not the current certified production identity.

The canonical immutable mapping for historical tags is `docs/RELEASE_TAGS.json`.

## Authority rule

If a historical release note conflicts with #1619, `docs/CURRENT_RELEASE_STATUS.md`, the immutable production tag, or exact deployed identity, the current authority wins.
