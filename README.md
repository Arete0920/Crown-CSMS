# Crown2026

Crown2026 is a multi-tenant school operations platform for Christian schools.

It is designed to support core SIS and operational workflows across admissions, enrollment, academics, billing, communications, portals, and mission-driven add-ons through a unified platform surface.

## Repository status

This repository reflects an actively developed product codebase and operational delivery system. Some areas are production-oriented, some are release-candidate hardening work, and some are internal implementation surfaces that are not intended to be treated as public APIs unless explicitly documented.

## Repository lineage

Crown2026 is the current active platform repository. Crown-Christian is retained as an archived legacy repository.

## What is in this repository

Top-level structure:

- `backend/` - core application backend and API surfaces
- `frontend/` - dashboard and UI applications
- `contracts/` - interface and contract artifacts between system layers
- `docs/` - architecture, operations, evidence, and governance documentation
- `scripts/` - utility and automation scripts
- `tools/` - engineering support tools
- `services/` - service-specific components, including wallet integration surfaces
- `.github/` - workflows, templates, and repository automation

## Product scope

Crown2026 covers school operations domains such as:

- SIS core
- admissions and enrollment
- academics and grade workflows
- billing and finance
- communications and portals
- mission-driven or institution-specific extensions

The exact module and endpoint surface evolves over time. Treat documented interfaces as authoritative over assumptions.

## Engineering approach

This repository is operated with a proof-first engineering discipline.

Expected changes should be:

- scoped
- reviewable
- accompanied by raw proof output
- validated through CI and workflow checks
- reversible through a clear rollback path

See:

- `CONTRIBUTING.md`
- `SECURITY.md`
- `docs/README.md`
- `docs/investor/README.md`
- `.github/pull_request_template.md`

## Quick start

### Prerequisites

You should have, at minimum:

- Python 3.11+
- Node.js 20+
- npm
- Git

Additional services or credentials may be required depending on which surfaces you run locally.

### Environment

Start from the example environment file where applicable:

```bash
cp .env.local.example .env.local
```

Then populate any required variables for the backend, frontend, and external integrations you intend to use.

### Backend

The canonical Django management entrypoint is:

```bash
python backend/manage.py check
```

Typical backend startup flow:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python backend/manage.py check
python backend/manage.py migrate
python backend/manage.py runserver
```

### Frontend

Typical frontend startup flow:

```bash
cd frontend
npm install
npm run dev
```

If the repository contains multiple frontend packages or apps, use the package-specific README or `package.json` scripts for the exact command.

## Testing and proof

Before opening a pull request, contributors should run the smallest relevant validation set for the area being changed.

Minimum local proof should usually include:

```bash
git status -sb
git diff --stat
python backend/manage.py check
```

Additional frontend, API, workflow, or end-to-end proof may be required depending on the blast radius of the change.

## Contribution model

This repository is not an ungoverned public contribution surface.

External readers are welcome. Proposed code changes should follow the contribution, proof, and security rules documented in:

- `CONTRIBUTING.md`
- `SECURITY.md`

## Security and disclosure

Do not open public issues for suspected vulnerabilities, secrets, or sensitive operational findings.

Use the private reporting path documented in `SECURITY.md`.

## License and usage

This repository is proprietary unless a separate license file explicitly states otherwise.

No right to use, copy, modify, distribute, sublicense, or create derivative works is granted except by prior written permission.

See `NOTICE.md` or `LICENSE` for controlling terms.

## Documentation map

Recommended document entrypoints:

- `docs/README.md`
- `docs/architecture/README.md`
- `docs/operations/README.md`
- `docs/security/README.md`
- `docs/evidence/README.md`
- `docs/investor/README.md`

## Contact

Repository owner or maintainer:

- John TC Megahan
- Website: [Arete Advisory Group](https://www.areteadvisorygroup.org)
- LinkedIn: [John Megahan](https://www.linkedin.com/in/john-megahan-935784232)
- `REPLACE_WITH_MAINTAINER_NAME`
- `REPLACE_WITH_MAINTAINER_EMAIL`
