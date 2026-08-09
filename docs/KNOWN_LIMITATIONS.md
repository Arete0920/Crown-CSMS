# CROWN Known Limitations and Release Disposition

**Last reconciled:** 2026-08-09  
**Certified backend:** `ce12c9536ec85346b2446018fa8bfe27edb3ffa0`  
**Immutable tag:** `prod-deploy-20260808-ce12c95`  
**Controlling authority:** GitHub issue #1619

## Certified-scope limits

- Certification is bounded to the exact backend, dashboard source, deployment runs, Heritage tenant, personas, routes, and retained evidence in `docs/CURRENT_RELEASE_STATUS.md`.
- Auditor is not represented in the current 18-row matrix.
- Current development `main` is not automatically the deployed identity.
- Source presence does not establish completion of every optional integration or future capability.
- External payment processing is not selected, contracted, enabled, or certified.

## Disclosed successor and maturity work

- measured rollback and isolated operational-backup restore;
- exhaustive credential rotation, revocation, failed-rotation recovery, and break-glass;
- expanded monitoring escalation and incident tabletop;
- vendor, DPA, region, subprocessor, jurisdiction, and contractual reconciliation;
- correction, export, deletion, legal-hold, and restored-backup lifecycle exercises;
- deferred historical rewrite of the retired key;
- payment-provider implementation and activation;
- buyer-controlled account creation, transfer, and seller-access removal.

CROWN is not represented as FERPA certified, COPPA certified, regulator approved, universally compliant, or legally approved for every intended market.
