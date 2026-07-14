# CROWN Developer Setup

**Status:** Canonical  
**Owner:** CROWN Engineering  
**Purpose:** One source of truth for local development setup.

This guide is editor-neutral. PyCharm, another approved editor, or a terminal-based environment may be used. No specific editor or paid subscription is required.

## 1. Repository access

CROWN is private. Access requires explicit collaborator authorization.

```bash
git clone https://github.com/tcmegahan/Crown2026.git
cd Crown2026
```

Work from an isolated branch or worktree. Do not commit directly to `main`.

## 2. Python environment

Use a repository-root `.venv`.

Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

## 3. Frontend dependencies

```bash
cd frontend/dashboards
npm ci
cd ../..
```

Use the Node and npm versions required by the current package and CI configuration. Do not upgrade dependencies as part of unrelated work.

## 4. Local configuration and secrets

Use only local placeholder or development values. Never commit passwords, API keys, tokens, production environment files, production database dumps, real school data, tenant secrets, private certificates, or confidential communications.

Where the local secrets template is present:

```bash
cp local.secrets.example local.secrets
```

Windows PowerShell:

```powershell
Copy-Item local.secrets.example local.secrets
```

## 5. Backend verification

```bash
python backend/manage.py check
python backend/manage.py migrate
pytest backend -m "not integration and not slow"
```

Do not create or apply new migrations unless the approved work explicitly includes migration changes.

## 6. Start the backend

```bash
python backend/manage.py runserver 127.0.0.1:8000 --noreload
```

Verify:

```bash
curl -i http://127.0.0.1:8000/health/
```

Expected: HTTP 200, a JSON response, and no traceback.

## 7. Start the frontend

In a second terminal:

```bash
cd frontend/dashboards
npm run dev -- --host 127.0.0.1 --port 3000
```

Verify:

```bash
curl -i http://127.0.0.1:3000/
```

Expected: HTTP 200.

## 8. Frontend verification

```bash
cd frontend/dashboards
npm run lint
npm run test:unit
npm run test:contracts
npm run build
```

Accessibility release check:

```bash
npm run test:release:a11y
```

Run focused tests before broad suites.

## 9. Pull-request closeout

Every pull request must identify:

- purpose and bounded scope;
- files changed and intentionally excluded;
- validation performed;
- known failures or limitations;
- independent-review status;
- rollback approach where applicable.

Human owners retain implementation, approval, security, and release accountability. Repository account attribution is not a substitute for a verified contributor record.

## 10. Handoff verification

A successor must be able to complete these steps from a clean clone without undocumented local assumptions. Before ownership transfer, independently verify setup, tests, deployment access, rollback, recovery, secrets access, and administrative control.

This guide does not certify pilot, production, compliance, or release approval. Use `docs/CURRENT_RELEASE_STATUS.md` for current release authority.
