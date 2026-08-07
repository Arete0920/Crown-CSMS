# CROWN Operations Documentation

**Status:** Canonical operations gateway  
**Last reconciled:** 2026-08-07  
**Certified release:** `17573fb649f74a3ba0f1b3fbc9e004108b3cf228`  
**Immutable tag:** `prod-deploy-20260804-17573fb`  
**Production deployment run:** `30944978175`  
**Controlling authority:** GitHub issue #1619

## Current posture

The bounded supported production release is certified and deployed. Repository technical certification, exact-identity deployment, runtime health, supported-role RBAC and tenant evidence, and payment containment passed as recorded in #1619 and `docs/CURRENT_RELEASE_STATUS.md`.

External payment processing remains disabled and fail closed. Buyer-specific turnover remains pending an identified buyer. Post-release source changes do not replace the certified production identity unless separately authorized, deployed, and certified.

## Evidence boundary

Documentation explains procedures; it does not prove an operational exercise occurred. The following remain disclosed residual maturity work unless separately executed and retained as evidence:

- full application rollback and isolated backup restore with measured RTO/RPO;
- exhaustive credential rotation, revocation, failed-rotation recovery, and break-glass;
- expanded monitoring escalation and incident tabletop;
- privacy, contract, vendor, region, and jurisdiction reconciliation;
- synthetic correction, export, deletion, legal-hold, and restored-backup lifecycle exercises.

These are not retroactive blockers to the bounded release decision accepted in #1619. They may become transaction, contract, insurer, counsel, or successor requirements.

## Runbook register

| Procedure | Current source | Verified status |
|---|---|---|
| Production deployment | Approved GitHub production workflow; run `30944978175` | Executed for certified release |
| Release identity and health | `docs/CURRENT_RELEASE_STATUS.md` and #1619 | Passed for certified release |
| Application rollback | `PRODUCTION_IMMUTABLE_ROLLBACK_DRILL.md` | Mechanics documented; full measured drill outstanding |
| Database restore | `ISOLATED_POSTGRES_RESTORE_DRILL.md` | Mechanics documented; operational-backup drill outstanding |
| Incident response | Repository guidance | Expanded tabletop outstanding |
| Secret rotation/revocation | Repository and external controls | Exhaustive exercise outstanding |
| Failed-rotation recovery | Repository guidance | Exercise outstanding |
| Break-glass access | Repository guidance | Exercise outstanding |
| Monitoring/alert delivery | Production health controls | Expanded delivery/acknowledgement exercise outstanding |

## Change and operating rules

- Confirm exact source, artifact, environment, workflow, and deployed identity before any operation.
- Stop on identity mismatch, migration failure, failed health or tenant checks, missing authority, or unsafe recovery target.
- Never infer current results from historical workflow output.
- Use approved GitHub workflows and protected environments.
- Keep payment processing disabled until a provider is selected, contracted, implemented, and certified.
- Preserve timestamps, operator identity, exact SHAs, decisions, and retained evidence.
- Treat `docs/ops/` as legacy supporting material unless explicitly reconciled here.

## Transaction operations

An authorized successor must verify external-service ownership, credentials, billing, backups, alert destinations, incident contacts, clean-clone reproducibility, and accepted residual risks. Buyer-specific transfer does not occur until successor identities and party acceptance exist.
