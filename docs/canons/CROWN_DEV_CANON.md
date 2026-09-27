# CROWN Local Development Canon

**Status:** current development authority pointer  
**Repository:** `Arete0920/Crown-CSMS`

## Purpose

Define the durable local-development rules for CROWN without depending on a specific person's workstation, directory layout, or operating system.

## Canonical setup

The controlling setup guide is:

- `docs/engineering/DEV_SETUP.md`

Supported development defaults:

- Python 3.12
- Node.js 20 LTS
- repository-root virtual environment or equivalent isolated Python environment
- frontend workspace at `frontend/dashboards`
- backend workspace at `backend`

## Repository root

Clone the current repository:

```bash
git clone https://github.com/Arete0920/Crown-CSMS.git
cd Crown-CSMS
```

Do not encode developer-specific absolute paths in committed documentation, scripts, or configuration.

## Backend

Use the supported Python environment and install:

```bash
pip install -r backend/requirements.txt
```

Run Django commands from the supported repository/backend context described in `DEV_SETUP.md`.

## Frontend

From `frontend/dashboards`:

```bash
npm ci
npm run dev
```

Use the committed lockfile. Do not document or depend on global package state.

## Secrets and credentials

- Never commit real credentials.
- Never commit personal access tokens.
- Never commit production or sandbox passwords.
- Use environment variables or the approved secret store.
- Demo credentials must be externally supplied, not hard-coded in source or documentation.

## Verification before commit

At minimum, run the checks appropriate to the changed surface:

- backend tests;
- frontend quality/build tests;
- schema/migration checks;
- tenant/authorization checks for affected domains;
- repository policy checks;
- exact-head CI before merge.

## Authority

If this file conflicts with:

1. `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`;
2. `docs/engineering/DEV_SETUP.md`;
3. `docs/CURRENT_RELEASE_STATUS.md`;

the more specific/current canonical authority controls.
