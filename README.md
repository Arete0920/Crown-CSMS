# CROWN

**Christian School Management Solution**

CROWN is a multi-tenant school management platform for Christian schools. The codebase covers admissions and enrollment, family and student records, academics and gradebook, billing and financial aid, communications, and school operations. School-scoped data and role-based permissions are core design requirements.

This repository contains application code, tests, and operational documentation. A module's presence in source does not establish that it is deployed or available to schools. For current release and operational status, see [Current Release Status](docs/CURRENT_RELEASE_STATUS.md).

## Repository layout

| Path | Responsibility |
| --- | --- |
| `backend/` | Django and Django REST Framework API, domain services, and data models |
| `frontend/dashboards/` | React and Vite interfaces for school and family workflows |
| `tests/` | Cross-cutting automated tests |
| `docs/` | Architecture, developer guidance, release controls, and operations |
| `.github/workflows/` | Continuous integration, security checks, and governed release workflows |
| `infra/`, `scripts/` | Infrastructure definitions and supporting utilities |

## Local development

Use Python **3.12** and Node.js **22.23.3** (the version in `.nvmrc`). PostgreSQL is the production-oriented database; Django defaults to SQLite for local development when `DATABASE_URL` is unset. Review [the development environment example](.env.example) before configuring optional services, and confirm that any configured database points to a local development instance. Keep credentials and school data out of version control.

From the repository root, set up and start the API:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python backend/manage.py check
python backend/manage.py migrate
python backend/manage.py runserver 127.0.0.1:8000 --noreload
```

On Windows, activate the environment with `.venv\Scripts\Activate.ps1`. Do not use production credentials or databases for local work.

In a separate terminal, start the dashboard:

```bash
cd frontend/dashboards
npm ci
npm run dev
```

The dashboard runs on port **3000** and proxies `/api` requests to the local API on port **8000** by default. Authenticated workflows also require synthetic school, user, and role data. See [Developer Setup](docs/engineering/DEV_SETUP.md) for the supported workflow and additional checks.

## Validation

Run focused checks before opening a pull request. The standard local baseline is:

```bash
pytest backend -m "not integration and not slow"
```

From `frontend/dashboards/`:

```bash
npm run lint
npm run test:unit
npm run test:contracts
npm run build
```

These commands do not replace the full CI, security, schema, tenant-isolation, and release checks. A change is reviewed and merged against its exact commit; deployment and runtime acceptance are verified separately.

## Engineering and operating standards

CROWN uses a single application platform with explicit school isolation, domain ownership, and authorization boundaries. Changes are made in scoped branches and reviewed through pull requests. Use synthetic records in development and testing. Never commit credentials, private school records, database dumps, or production configuration.

External integrations require their own configuration and verification. Payment processing is disabled pending the applicable contracting, integration, and operational authorization.

Key references:

- [Architecture Map](docs/architecture/ARCHITECTURE_MAP.md)
- [Current Release Status](docs/CURRENT_RELEASE_STATUS.md)
- [Known Limitations](docs/KNOWN_LIMITATIONS.md)
- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Operations Documentation](docs/operations/README.md)
- [Canonical Document Index](docs/canonical/CANONICAL_DOCUMENT_INDEX.md)

## Ownership and license

CROWN was created and is directed by TC Megahan. Specific contributor attribution follows the repository's [engineering accountability policy](docs/engineering/ENGINEERING_ACCOUNTABILITY_POLICY.md).

This repository is publicly accessible but is **not distributed under an open-source license**. See the [Public Repository Licensing Decision](docs/governance/PUBLIC_REPOSITORY_LICENSING_DECISION.md). Public visibility does not grant additional use, modification, or redistribution rights.
