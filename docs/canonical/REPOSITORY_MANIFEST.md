# CROWN Repository Manifest

**Status:** Canonical  
**Owner:** CROWN Engineering  
**Effective date:** 2026-07-28

## Purpose

This manifest explains the intended role of the repository's major areas after owner-transfer cleanup.

## Primary areas

| Path | Classification | Purpose |
|---|---|---|
| `backend/` | Runtime source | Django backend, APIs, domain logic, persistence, permissions, migrations, and backend tests. |
| `frontend/dashboards/` | Runtime source | Canonical browser application, dashboards, UI components, routes, frontend tests, and build configuration. Legacy or evidence-only frontend trees must not be treated as runtime source. |
| `.github/` | Repository governance | Pull-request templates, ownership rules, workflows, and GitHub configuration. |
| `docs/architecture/` | Architecture | System boundaries, runtime entrypoints, tenancy, integrations, and deployment design. |
| `docs/engineering/` | Engineering | Setup, contribution practices, testing, and engineering policy. |
| `docs/operations/` | Operations | Deployment, recovery, maintenance, rotation, incident, and operator procedures. |
| `docs/security/` | Security | Security policies, controls, hardening guidance, and evidence boundaries. |
| `docs/ownership/` | Ownership transfer | Successor handoff, external-service transfer, and release-restart requirements. |
| `docs/canonical/` | Document authority | Canonical document index, repository manifest, and authority rules. |
| `docs/provenance/` | Provenance | Human contribution, development lineage, and supporting attribution records. |
| `scripts/` | Active automation | Development, validation, maintenance, release, and recovery scripts still required by current workflows or operations. |
| `tools/` | Engineering tools | Repository and application utilities required by active engineering processes. |

## Root policy

The repository root should contain only immediate orientation, governance, build configuration, security, licensing, contribution, and canonical authority files. Temporary reports, proof dumps, copied conversations, local workstation records, personal paths, and superseded status snapshots do not belong at root.

## Retention rules

1. Keep source, tests, migrations, active configuration, and operationally required automation.
2. Keep documentation that explains architecture, setup, security, operation, recovery, and ownership transfer.
3. Do not commit generated audit output, test-result dumps, copied evidence packs, or local machine captures.
4. Do not retain marketing, valuation, buyer targeting, negotiation, or transaction-planning material in the engineering repository.
5. Remove retired scripts and dated release-control documents when their functional purpose has ended.
6. Never commit live secrets, production data, private certificates, or confidential customer information.
7. Workflow deletion or modification requires focused review because branch protections and required checks may depend on workflow names.
8. Security, authentication, tenancy, deployment, migrations, and package manifests require evidence-based change control.

## Handoff validation

An authorized successor should confirm from a clean clone that:

- repository navigation is understandable;
- local setup is reproducible;
- architecture and runtime boundaries are clear;
- active workflows do not reference deleted paths;
- required tests and builds run on one exact commit;
- deployment, rollback, restore, secret rotation, and incident procedures are understandable;
- external service ownership can be transferred without relying on personal workstation state or undocumented credentials.
