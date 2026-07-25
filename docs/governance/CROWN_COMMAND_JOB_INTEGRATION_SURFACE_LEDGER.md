# CROWN Command, Job, and Integration Surface Ledger

**Document ID:** CROWN-GOV-008  
**Status:** ACTIVE — Stage 1 Census in Progress  
**Parent authority:** `docs/governance/CROWN_BUYER_READY_COMPLETION_CANON.md`  
**Controlling issue:** #1587  
**Baseline repository SHA:** `6f0aec52cac2980e8dc9ecf04e5ac4d13a6d9cf4`  
**Verification date:** 2026-07-25

## Purpose

Control the non-request execution surface that can create, mutate, export, purge, seed, reconcile, prove, or integrate CROWN data. Presence in source does not establish authorization, tenant safety, production scheduling, operational ownership, or release readiness.

## Verified surface classes

| Surface class | Verified source examples | Current controlled finding | Required proof |
|---|---|---|---|
| Django management commands | `backend/*/management/commands/*.py` | Repository search identifies dozens of commands spanning demo seeding, permission setup, schema repair, retention, finance, billing, academics, sandbox, proof, and readiness operations | Exact manifest; command name; owning app; mutation class; environment policy; tenant boundary; idempotency; rollback; test |
| Demo and sandbox seed commands | `backend/core/management/commands/seed_demo.py`; `backend/core/management/commands/sandbox_seed.py`; `backend/sandbox_demo/**/management/commands/*.py` | Multiple seed and invite/proof command families exist, including duplicate command filenames under nested sandbox package paths | Resolve Django command winner, intended package, deterministic data contract, production denial, and duplicate-path disposition |
| Data retention and lifecycle commands | `backend/core/management/commands/purge_expired_records.py`; `backend/apps/compliance/management/commands/compliance_retention_review.py` | Retention-affecting commands exist but are not yet mapped to approved schedules, legal policy, dry-run behavior, or evidence retention | Policy owner; scope; dry run; audit log; restore path; schedule; operational drill |
| Finance and billing commands | `backend/billing/management/commands/enforce_grace_period.py`; `backend/billing/management/commands/seed_billing_demo.py`; `backend/finance_setup/management/commands/seed_finance_setup_demo.py` | Financial-state mutation and seed surfaces require separate provider-neutral and excluded-payment boundaries | Permission; tenant scope; accounting invariants; provider exclusion; replay safety; rollback |
| Schema and diagnostic commands | `backend/crown_api/management/commands/fix_schema_drift.py`; `backend/crown_api/management/commands/diagnose_db_tables.py` | Commands may inspect or alter schema-adjacent state and therefore require explicit environment and change-control policy | Production policy; backup prerequisite; dry run; migration authority; logging; recovery |
| Proof and readiness commands | `backend/crown_api/management/commands/proof_phase3_runtime.py`; `backend/core/management/commands/crown_readiness_check.py`; `backend/sandbox_demo/management/commands/sandbox_proof_gate.py` | Proof commands exist, but command output alone is not production authority and must bind to exact SHA, environment, and evidence artifact | Immutable identity; non-self-certification rule; artifact path; failure semantics; freshness |
| Celery/background tasks | `backend/comms/tasks.py` | At least one task module is verified; complete task discovery and scheduler ownership remain open | Exact task manifest; trigger; queue; retry; idempotency; tenant context; dead-letter and monitoring proof |
| Integration application surface | `backend/integrations/apps.py`; `backend/integrations/models.py`; `backend/integrations/api/views.py`; `backend/integrations/oneroster.py` | Installed integration domain includes models, API views, and OneRoster logic; enabled-versus-installed state is unresolved | Provider inventory; credentials; environment enablement; data flow; retry; audit; ownership; contract tests |
| Real-provider integration package | `backend/integrations_real/apps.py` | A separate real-integration package exists and must not be conflated with configured-safe or simulated integration behavior | Installation state; feature flag; secret source; network boundary; fail-closed proof; operational owner |
| Payment-provider adapters | `backend/advancement/payments/providers.py` | Provider abstraction exists outside the central integrations package; external payment execution remains excluded unless separately authorized | Provider list; disabled state; call sites; secret boundary; webhook ownership; negative tests |
| Repository workflow jobs | `.github/workflows/*` | PR #1612 exact head triggered 29 workflow runs across tests, security, route, schema, release, evidence, UI, accounting, dependency, and promotion controls | Canonical workflow inventory; trigger matrix; required/advisory classification; overlap; artifact authority; retirement decision |

## High-risk command families requiring first-pass classification

1. Commands that create users, permissions, invitations, or privileged accounts.
2. Commands that modify schema, repair drift, or bypass normal migration flow.
3. Commands that purge, expire, retain, archive, or otherwise remove records.
4. Commands that mutate billing, finance, payment, aid, enrollment, or academic records.
5. Commands that seed production-like identities, passwords, tenants, or datasets.
6. Commands that produce release, runtime, sandbox, or readiness proof.
7. Commands with duplicate names across installed or potentially installed Django apps.
8. Commands invoked by workflows, schedulers, container startup, deployment, or operator runbooks.

## Verified duplicate-path concern

Repository search identifies sandbox command filenames under both:

- `backend/sandbox_demo/management/commands/`
- `backend/sandbox_demo/sandbox_demo/management/commands/`

The source census must determine which package is installed, whether both command sets are discoverable, whether names collide, and whether one path is stale or superseded. No winner or defect is asserted until executable Django discovery proves it.

## Workflow control requirements

Each active workflow must be mapped to exactly one primary authority class:

- required merge gate;
- security/advisory evidence;
- source contract gate;
- release-candidate promotion gate;
- deployed-runtime proof;
- sandbox/demo proof;
- scheduled maintenance;
- manual operator workflow;
- superseded or duplicate.

Workflow success must not be combined across different commit SHAs. Historical artifacts do not prove current readiness.

## Required next executable evidence

1. Generate an exact Django command manifest from the configured application registry and record command winner paths.
2. Detect duplicate command names and fail the census when ownership is ambiguous.
3. Extract all Celery tasks, scheduled invocations, signals, and background runners.
4. Map commands and tasks to models, services, tenant context, permissions, mutation type, and tests.
5. Inventory installed, enabled, disabled, simulated, and excluded integrations by environment.
6. Generate a canonical workflow trigger/job/artifact manifest directly from `.github/workflows/`.
7. Classify every workflow as required, advisory, runtime proof, manual, scheduled, duplicate, or superseded.
8. Bind all generated evidence to an immutable repository SHA.

## Release authority

This ledger is a source-control census. It does not authorize command execution, integration enablement, scheduling, data mutation, release promotion, buyer readiness, or production. Production remains **NOT APPROVED**.
