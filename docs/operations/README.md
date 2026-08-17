# CROWN Operations Documentation

**Status:** Canonical operations gateway  
**Last reconciled:** 2026-08-17  
**Handoff-refresh base `main`:** `f9bf6b4143e707f93ec8d6ce319327ddc7d3e2a0`

## Operating boundary

Confirm exact source, artifact, environment, tag, and deployed identity before every production operation. Stop on identity mismatch, migration failure, failed health or tenant checks, missing authority, or unsafe recovery targets.

Use approved GitHub workflows and protected environments. Documentation and workflow source explain procedures; neither proves that a current operational drill occurred.

## Current turnover evidence boundary

| Procedure | Current disposition |
|---|---|
| Current Crown-CSMS repository source | `main` at handoff-refresh base `f9bf6b4143e707f93ec8d6ce319327ddc7d3e2a0` |
| Security/repository hardening | PRs #97 and #98 merged |
| Current deployed runtime identity | Not verified in the current turnover sequence |
| Application rollback | Runnable immutable mechanics; current authorized execution evidence outstanding |
| Database restore | Isolated PostgreSQL mechanics proven; release-linked operational-backup evidence outstanding |
| Credential/break-glass exercise | Outstanding unless separately evidenced and accepted |
| Expanded incident/alert exercise | Outstanding unless separately evidenced and accepted |
| Payment processing | Disabled / fail closed |

Historical predecessor deployment and dashboard evidence may be retained as provenance, but it must not be substituted for current Crown-CSMS runtime or recovery evidence.

## Primary operational references

- `PRODUCTION_RECOVERY_PATH.md`
- `PRODUCTION_RECOVERY_DECISION_TREE.md`
- `PRODUCTION_IMMUTABLE_ROLLBACK_DRILL.md`
- `ISOLATED_POSTGRES_RESTORE_DRILL.md`
- `../DISASTER_RECOVERY_POLICY.md`
- `../CURRENT_RELEASE_STATUS.md`

The owner handoff requires the successor to understand which procedures are proven mechanics, which have current operational evidence, and which remain to be executed or explicitly accepted as residual risk.
