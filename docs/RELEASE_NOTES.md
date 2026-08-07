# CROWN Release Notes

## Certified bounded production release — 2026-08-04

- **Source:** `17573fb649f74a3ba0f1b3fbc9e004108b3cf228`
- **Immutable tag:** `prod-deploy-20260804-17573fb`
- **Production deployment run:** `30944978175`
- **Authority:** GitHub issue #1619
- **Status:** Certified and deployed

### Verified release scope

- terminal exact-SHA repository, security, dependency, schema, frontend, backend, and release gates;
- production migration and deployment through the approved exact-identity path;
- deployed build identity and health verification;
- bounded runtime, tenant, RBAC, route, role, and production-bundle certification;
- backend bounded regression: 4,419 passed, 8 skipped, zero failures;
- frontend tests and production build;
- external payment processing disabled and fail closed.

### Certified active dashboard roles

- `compliance-director`
- `crown-master`
- `deputy-head`
- `headteacher`
- `school-admin`
- `teacher`

Parent, student, board, and auditor dashboards are not claimed as certified active personas.

### Deferred and transaction-specific boundaries

External payment processing remains disabled and deferred to a new owner. Buyer-specific accounts, credential transfer, seller-access removal, contracts, legal acceptance, and payment-provider activation remain pending an identified buyer.

Residual operational maturity work is disclosed in `docs/KNOWN_LIMITATIONS.md` and #1619.

## Post-release change control

Later commits on `main` do not redefine the certified production identity unless separately authorized, deployed, and certified. Each post-release repair must identify its own exact head, tests, review status, and runtime-proof requirements.

## Historical releases

### `crown-0.3.1-prod-pipeline-fix` — 2026-01-27

Historical pipeline milestone at `a1c4c42a381e03587c784bd995ec8fd6c33aeee9`. It is not the current certified production identity.

### `crown-0.3.0-spine-complete` — 2026-01-27

Historical tenant-isolation and CI foundation at `340c7e3fbb882eb4886fbfbbe8e648f3866e5178`. It is not the current certified production identity.

The canonical immutable mapping for historical tags is `docs/RELEASE_TAGS.json`.

## Authority rule

If a historical release note conflicts with #1619, `docs/CURRENT_RELEASE_STATUS.md`, the immutable production tag, or exact deployed identity, the current authority wins.
