# CROWN Architecture Documentation

**Status:** Canonical architecture gateway  
**Owner:** CROWN Engineering  
**Effective date:** 2026-07-14

## Authority

This file is the required entrypoint for CROWN architecture documentation. Material elsewhere in `docs/architecture/` is supporting unless the canonical document index explicitly assigns it authority.

Architecture documents describe system structure and constraints. They do not independently certify release readiness, production deployment, operational recovery, or module completion.

## System reading order

1. `../../README.md` — repository authority and release posture.
2. `../canonical/REPOSITORY_MANIFEST.md` — repository boundaries and document classification.
3. This file — architecture navigation and authority rules.
4. `../engineering/DEV_SETUP.md` — supported development setup.
5. `../operations/README.md` — deployment, recovery, and operator navigation.
6. `../CURRENT_RELEASE_STATUS.md` — current release authority.

## Architecture domains

Use this directory for durable descriptions of:

- platform and subsystem boundaries;
- frontend, backend, API, and persistence responsibilities;
- multi-tenant isolation and trusted school context;
- authentication, authorization, and role boundaries;
- domain modules and shared service contracts;
- external integrations and payment-provider boundaries;
- deployment topology and runtime dependencies;
- architecture decisions, constraints, and supersession records.

## Classification rules

- New architecture documents must identify their status as `CANONICAL`, `SUPPORTING`, `HISTORICAL`, or `SUPERSEDED`.
- A document is not canonical merely because its filename contains `final`, `complete`, `master`, or a recent date.
- Completion matrices and certification evidence report verification state; they do not define architecture.
- Generated diagrams, audits, and proof artifacts are supporting evidence unless explicitly promoted through the canonical index.
- Conflicting documents must be reconciled through a focused pull request that names the controlling source and preserves prior history.

## Current limitations

The directory still requires a file-by-file inventory. Until that inventory is complete, this gateway controls navigation and classification, but it does not assert that every architecture document is current or correctly placed.

Do not delete or relocate historical architecture material without confirming references, preserving Git history, and identifying the controlling replacement.