# CROWN Operations Documentation

**Status:** Canonical operations gateway  
**Last reconciled:** 2026-08-18  
**Current repository identity:** governed by `../CURRENT_RELEASE_STATUS.md` and exact current `main`

## Operating boundary

Confirm exact source, artifact, environment, tag, and deployed identity before every production operation. Stop on identity mismatch, migration failure, failed health or tenant checks, missing authority, or unsafe recovery targets.

Use approved GitHub workflows and protected environments. Documentation and workflow source explain procedures; neither proves that a current operational drill occurred.

Completed predecessor/successor engineering issue programs and their issue numbers are historical provenance unless the current release status explicitly adopts them as active operational authority.

## Current turnover evidence boundary

| Procedure | Current disposition |
|---|---|
| Current Crown-CSMS repository source | Exact current `main`, governed by `docs/CURRENT_RELEASE_STATUS.md` |
| Repository engineering/certification | Current exact-SHA repository evidence governs; historical issue trackers are not current operational authority |
| Current deployed runtime identity | Not verified in the current turnover sequence |
| Application rollback | Runnable immutable mechanics; current authorized execution evidence outstanding |
| Database restore | Isolated PostgreSQL mechanics proven; release-linked operational-backup evidence outstanding |
| Credential/break-glass exercise | Outstanding unless separately evidenced and accepted |
| Expanded incident/alert exercise | Outstanding unless separately evidenced and accepted |
| Successor account/access transition | Pending authorized transfer execution and acceptance |
| Payment processing | Disabled / fail closed |

Historical predecessor deployment, recovery, issue, and dashboard evidence may be retained as provenance, but it must not be substituted for current Crown-CSMS runtime or recovery evidence.

## Primary operational references

- `PRODUCTION_RECOVERY_PATH.md`
- `PRODUCTION_RECOVERY_DECISION_TREE.md`
- `PRODUCTION_IMMUTABLE_ROLLBACK_DRILL.md`
- `ISOLATED_POSTGRES_RESTORE_DRILL.md`
- `../DISASTER_RECOVERY_POLICY.md`
- `../CURRENT_RELEASE_STATUS.md`

The owner handoff requires the successor to understand which procedures are proven mechanics, which have current operational evidence, and which remain to be executed or explicitly accepted as residual risk.


## School implementation

Use `SCHOOL_IMPLEMENTATION_RUNBOOK.md` as the canonical contract-to-go-live operating path for school implementations.
