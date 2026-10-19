# CROWN Engineering Onboarding

This guide provides a short orientation to the repository. [Developer Setup](DEV_SETUP.md) is the source for local dependencies, commands, and checks; [Current Release Status](../CURRENT_RELEASE_STATUS.md) governs release claims.

## Start with the supported setup

- Use Python 3.12 and Node.js 22.23.3, as specified by the repository version files and [Developer Setup](DEV_SETUP.md).
- Install frontend dependencies with `npm ci` in `frontend/dashboards/`; do not replace the lockfile-based installation with `npm install`.
- Use [Local Quick Start](../LOCAL_QUICKSTART.md) for Windows and the fictional Heritage demonstration.
- Supply local configuration using approved environment variables or ignored local files. The repository does not contain a reusable credential file, and development must not use a production school database.

## Read the codebase

| Area | Responsibility |
| --- | --- |
| `backend/` | Django API, domain services, permissions, data models, and migrations |
| `frontend/dashboards/` | React application, routes, interfaces, and frontend tests |
| `tests/` and `backend/*/tests/` | Automated regressions and contract checks |
| `docs/architecture/` | Accepted architecture, canonical tenancy, and domain boundaries |
| `docs/operations/` | Environment procedures, deployment, recovery, and rollback |
| `.github/workflows/` | Required verification and governed deployment workflows |

Use the [Architecture Map](../architecture/ARCHITECTURE_MAP.md) and its accepted architecture-decision index before modifying shared services or trust boundaries.

## First change

1. Confirm current `main`, the relevant issue or requirement, and the controlling architecture and policy documents.
2. Make a small, independently reversible change on its own branch; do not push directly to protected `main`.
3. Add focused regression coverage when application behavior changes. Run the corresponding checks in [Developer Setup](DEV_SETUP.md).
4. Open one pull request for the coherent outcome, with the exact source identity, validation, unresolved evidence, and rollback action.
5. Merge only after the current PR head satisfies applicable gates and the authorized owner accepts the change.

See [Repository Workflow](REPOSITORY_WORKFLOW.md), [Contributing](../../CONTRIBUTING.md), and [Engineering Accountability](ENGINEERING_ACCOUNTABILITY_POLICY.md).

## Operating constraints

- Resolve and authorize school scope before protected reads or writes. `request.crown_tenant` is the canonical request tenant context; caller-supplied school headers alone do not authorize access.
- Maintain permission, tenant-isolation, audit, and error-handling safeguards. Do not suppress test or runtime failures to obtain passing checks.
- Preserve applied migration history and stable Django app labels; use an approved forward migration for schema changes.
- Never commit school records, live credentials, private certificates, database dumps, or confidential communications.
- External payment processing remains disabled until separately authorized and verified.
- A passing repository check does not prove deployment, recovery, or live school behavior.

Report suspected vulnerabilities privately under the [Security Policy](../../SECURITY.md).
