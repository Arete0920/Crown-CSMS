# CROWN Operations Documentation

**Status:** Canonical operations gateway  
**Last reconciled:** 2026-08-09  
**Certified backend:** `ce12c9536ec85346b2446018fa8bfe27edb3ffa0`  
**Immutable tag:** `prod-deploy-20260808-ce12c95`  
**Production run:** `31287503791`  
**Dashboard run:** `31289219093`

## Operating boundary

Confirm exact source, artifact, environment, tag, and deployed identity before every production operation. Stop on identity mismatch, migration failure, failed health or tenant checks, missing authority, or unsafe recovery targets.

Use approved GitHub workflows and protected environments. Current documentation explains procedures; it does not prove an operational drill occurred.

## Current evidence

| Procedure | Status |
|---|---|
| Production deployment and migration | Executed successfully in run `31287503791` |
| Backend identity and health | Passed for `ce12c9536ec85346b2446018fa8bfe27edb3ffa0` |
| Dashboard deployment and live certification | Passed in run `31289219093`; 18/18 surfaces |
| Application rollback | Mechanics documented; measured full drill outstanding unless separately evidenced |
| Database restore | Mechanics documented; operational-backup drill outstanding unless separately evidenced |
| Credential/break-glass exercise | Outstanding unless separately evidenced |
| Expanded incident/alert exercise | Outstanding unless separately evidenced |

Payment processing remains disabled until a provider is selected, contracted, implemented, and certified.
