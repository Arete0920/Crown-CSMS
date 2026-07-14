# CROWN Repository Manifest

**Status:** Canonical  
**Owner:** CROWN Engineering  
**Effective date:** 2026-07-14

## Purpose

This manifest explains the intended role of the repository's major areas. It is a navigation and classification authority, not a claim that every existing file has already been reviewed or correctly placed.

## Primary areas

| Path | Classification | Purpose |
|---|---|---|
| `backend/` | Runtime source | Django backend, APIs, domain logic, persistence, permissions, migrations, and backend tests. |
| `frontend/` | Runtime source | Browser applications, dashboards, UI components, routes, frontend tests, and build configuration. |
| `.github/` | Repository governance | Pull-request templates, ownership rules, workflows, and GitHub configuration. |
| `docs/architecture/` | Architecture | System boundaries, runtime entrypoints, tenancy, integrations, and deployment design. |
| `docs/engineering/` | Engineering | Setup, contribution practices, testing, and engineering policy. |
| `docs/operations/` and `docs/ops/` | Operations | Deployment, recovery, maintenance, rotation, and operator procedures. |
| `docs/security/` | Security | Security policies, controls, and evidence boundaries. |
| `docs/canonical/` | Document authority | Canonical document index and authority rules. |
| `docs/provenance/` | Historical provenance | Human contribution, development lineage, and supporting attribution records. |
| `scripts/` | Automation source | Development, validation, maintenance, release, and audit scripts. |
| `tools/` | Engineering tools | Repository and application utilities. |

## Historical and generated material

These areas may contain useful evidence but are not automatically current authority:

| Path pattern | Classification |
|---|---|
| `audit-artifacts/` | Generated or historical evidence |
| `AUDIT_PACK/` | Historical or generated evidence |
| `docs/release/evidence/` | Release evidence subject to retention review |
| `docs/release/live-audit/` | Generated or historical evidence |
| `docs/repo-cleanup/` | Historical cleanup records |
| `docs/completion/` | Mixed-age status material; verify freshness before relying on it |

## Root policy

The repository root should contain only immediate orientation, governance, build configuration, security, and canonical authority files. Temporary reports, proof dumps, copied conversations, local workstation records, and superseded status snapshots do not belong at root.

## Cleanup rules

1. Preserve history before deleting or relocating material.
2. Do not mix runtime changes with repository restructuring.
3. Generated evidence is not architectural authority.
4. Old status documents are not current merely because they remain in the tree.
5. Superseded canonical documents must identify their replacement.
6. Workflow deletion or modification requires focused review.
7. Security, authentication, tenancy, deployment, migrations, and package manifests require evidence-based change control.

## Handoff validation

Johnny, Evan, or another designated reviewer should confirm from a clean clone that the repository start path, runtime boundaries, canonical documents, setup procedure, and operational ownership are understandable without undocumented assumptions.
