# CROWN Operations Documentation

**Status:** Canonical operations gateway  
**Owner:** CROWN Engineering  
**Effective date:** 2026-07-14

## Authority

This file is the entrypoint for CROWN deployment, release, incident, maintenance, rollback, restore, and operational-readiness documentation.

Documents under `docs/operations/` may be treated as current operational guidance only when they are linked from this gateway or explicitly designated canonical by the Canonical Document Index.

Material under `docs/ops/` is legacy supporting material pending file-by-file reconciliation. It may contain useful procedures or historical evidence, but it does not override this gateway, the current release-status document, or a later approved runbook.

Release evidence under `docs/release/` supports decisions; it is not, by itself, an operating procedure.

## Required operating flow

A reviewer or successor should be able to follow one documented path through:

1. environment and access prerequisites;
2. configuration and secret dependencies;
3. pre-deployment validation;
4. deployment execution;
5. health and tenant-integrity verification;
6. rollback decision and execution;
7. database restore or manual recovery fallback;
8. incident escalation and evidence capture;
9. release-authority reconciliation.

## Current posture

CROWN remains a controlled sandbox release candidate unless `docs/CURRENT_RELEASE_STATUS.md` or a later authorized release record states otherwise.

Documentation does not prove that a procedure works. Deployment, rollback, restore, secret rotation, and break-glass procedures require current execution evidence before production approval.

## Active work and blockers

- Production recovery and rollback proof: issue #1270.
- Release notes, changelog, and runbook posture: issue #1277.
- Production secrets management and Vault readiness: issue #1294.
- Secrets rotation, audit, and break-glass runbook: issue #1296.
- Final release-authority reconciliation: issue #1275.

## Consolidation rule

New operational documents belong under `docs/operations/`. Do not add new material to `docs/ops/`.

Existing files under `docs/ops/` must be inventoried before relocation or deletion. Each file must be classified as canonical, supporting, historical, superseded, generated evidence, or obsolete. Preserve Git history and identify replacements when material is superseded.

## Review standard

Johnny, Evan, or another designated reviewer should validate from a clean clone that the operational path is understandable without undocumented assumptions. Ownership, credentials, external services, and production access remain subject to the verified handoff session.