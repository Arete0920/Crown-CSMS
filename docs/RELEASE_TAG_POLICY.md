# CROWN Release Tag Policy

**Last reconciled:** 2026-08-17

## Immutability

Every published release tag is immutable. Do not move, delete/recreate, or force-update a release tag. A follow-on release receives a new tag at a new exact commit.

## Current Crown-CSMS authority

No historical Crown2026 or predecessor tag is current Crown-CSMS turnover authority. The selected current source/release identity must be recorded in `docs/CURRENT_RELEASE_STATUS.md` and Crown-CSMS issue #14, then independently proven through build, deployment, runtime identity, health, monitoring, and required recovery evidence before it is represented as production deployed.

## Historical predecessor production tag

| Tag | Commit | Status |
|---|---|---|
| `prod-deploy-20260808-ce12c95` | `ce12c9536ec85346b2446018fa8bfe27edb3ffa0` | Historical predecessor/bounded production evidence |

Historical deployment run: `31287503791`.

## Naming

- Certified production deployment: `prod-deploy-YYYYMMDD-<short-sha>`
- Historical product milestone: `crown-X.Y.Z-<descriptor>`
- Hotfix milestone: `crown-X.Y.Z-hotfix-<issue>`

A historical `crown-*` or `prod-deploy-*` tag does not become current Crown-CSMS production identity unless a current authorized release record explicitly selects, deploys, verifies, and accepts that exact identity.

## Creation and verification

1. Resolve and record the full selected release SHA.
2. Require terminal exact-SHA validation and applicable authorization.
3. Create the annotated immutable tag once.
4. Push without force.
5. Resolve the remote tag and verify it matches the approved full SHA.
6. Deploy only through the approved protected workflow.
7. Verify repository SHA, artifact/image identity, runtime build identity, database health, application health, and monitoring.
8. Execute or explicitly disposition required rollback/restore evidence for the same release identity.
9. Record the tag, SHA, deployment run, runtime evidence, recovery evidence, and decision in Crown-CSMS issue #14 or its authorized successor control record.

## Historical tags

| Tag | Commit | Classification |
|---|---|---|
| `crown-0.3.0-spine-complete` | `340c7e3fbb882eb4886fbfbbe8e648f3866e5178` | Historical foundation |
| `crown-0.3.1-prod-pipeline-fix` | `a1c4c42a381e03587c784bd995ec8fd6c33aeee9` | Historical pipeline milestone |

The immutable mapping for historical tags is `docs/RELEASE_TAGS.json`; historical mappings must remain internally consistent.

## Enforcement

Reject any change that moves or recreates an existing tag, represents a historical milestone as current production, deploys an unapproved identity, or allows documentation to contradict the controlling exact release identity.
