# CROWN Release Tag Policy

**Last reconciled:** 2026-08-11

## Immutability

Every published release tag is immutable. Do not move, delete/recreate, or force-update a release tag. A follow-on release receives a new tag at a new exact commit.

## Current successor production tag

None. `Crown-CSMS` has not published a successor production tag; prior production tags remain historical authority in preserved `Crown2026`.

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

Pre-migration tags remain in preserved `Crown2026`; `docs/RELEASE_TAGS.json` registers only immutable release tags published by `Crown-CSMS`.

## Enforcement

Reject any change that moves or recreates an existing tag, represents a historical milestone as current production, deploys an unapproved identity, or allows documentation to contradict the controlling exact release identity.
