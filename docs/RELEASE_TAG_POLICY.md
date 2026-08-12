# CROWN Release Tag Policy

**Last reconciled:** 2026-08-11

## Immutability

Every published release tag is immutable. Do not move, delete/recreate, or force-update a release tag. A follow-on release receives a new tag at a new exact commit.

## Historical predecessor production tag — Crown2026 only

| Tag | Commit | Status |
|---|---|---|
| `prod-deploy-20260808-ce12c95` | `ce12c9536ec85346b2446018fa8bfe27edb3ffa0` | Certified production source |

Production deployment run: `31287503791`  
Controlling authority: GitHub issue #1619

## Naming

- Certified production deployment: `prod-deploy-YYYYMMDD-<short-sha>`
- Historical product milestone: `crown-X.Y.Z-<descriptor>`
- Hotfix milestone: `crown-X.Y.Z-hotfix-<issue>`

A historical `crown-*` milestone does not become the current production identity unless an authorized release record explicitly designates and deploys it.

## Creation and verification

1. Resolve and record the full release SHA.
2. Require terminal exact-SHA validation and authorization.
3. Create the annotated immutable tag once.
4. Push without force.
5. Resolve the remote tag and verify it matches the approved full SHA.
6. Deploy only through the approved protected workflow.
7. Verify repository SHA, artifact/image identity, runtime build identity, and health.
8. Record the tag, SHA, deployment run, and decision in #1619 or its authorized successor.

## Historical tags

| Tag | Commit | Classification |
|---|---|---|
| `crown-0.3.0-spine-complete` | `340c7e3fbb882eb4886fbfbbe8e648f3866e5178` | Historical foundation |
| `crown-0.3.1-prod-pipeline-fix` | `a1c4c42a381e03587c784bd995ec8fd6c33aeee9` | Historical pipeline milestone |

The canonical immutable mapping for historical tags is `docs/RELEASE_TAGS.json`; this table must match it exactly.

## Enforcement

Reject any change that moves or recreates an existing tag, represents a historical milestone as current production, deploys an unapproved identity, or allows documentation to contradict the controlling exact release identity.
