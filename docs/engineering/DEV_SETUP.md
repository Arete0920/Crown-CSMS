# CROWN Developer Setup

**Status:** Canonical  
**Owner:** CROWN Engineering  
**Purpose:** One source of truth for local development setup.

CROWN local development uses VS Code, GitHub, and PowerShell where appropriate. No paid coding-assistant subscription is required. Terminal commands remain authoritative; editor features are conveniences rather than release evidence.

## 1. Repository access

CROWN is private. Access requires explicit collaborator authorization.

```bash
git clone https://github.com/tcmegahan/Crown2026.git
cd Crown2026
```

Work from an isolated branch or worktree. Do not commit directly to `main`.

## 2. VS Code workspace

Open the repository root in VS Code so backend, frontend, scripts, tests, and documentation remain visible in one workspace.

Windows PowerShell:

```powershell
code .
```

Use the checked-in workspace configuration only when it is current and understood. Review extension recommendations before installing them. Local editor state is not repository evidence.

## 3. Python environment

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

## 4. Frontend dependencies

```bash
cd frontend/dashboards
npm ci
cd ../..
```

Use the Node and npm versions required by the current package and CI configuration. Do not upgrade dependencies as part of unrelated work.

## 5. Local configuration and secrets

Use only local placeholder or development values. Never commit passwords, API keys, tokens, production environment files, production database dumps, real school data, tenant secrets, private certificates, or confidential communications.

Where the local secrets template is present:

```bash
cp local.secrets.example local.secrets
```

Windows PowerShell:

```powershell
Copy-Item local.secrets.example local.secrets
```

## 6. Backend verification

```bash
python backend/manage.py check
python backend/manage.py migrate
pytest backend -m "not integration and not slow"
```

Do not create or apply new migrations unless the approved work explicitly includes migration changes. Production migration authority is controlled separately from ordinary web startup.

## 7. Start the backend

```bash
python backend/manage.py runserver 127.0.0.1:8000 --noreload
```

Verify:

```bash
curl -i http://127.0.0.1:8000/health/
```

Windows PowerShell may use `Invoke-RestMethod` or `curl.exe` explicitly.

Expected: HTTP 200, a JSON response, and no traceback.

## 8. Start the frontend

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

## 9. Frontend verification

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

## 10. Controlled local work

Before editing, record the current branch, HEAD, exact task, expected files, excluded files, and validation commands. Avoid broad copy-and-paste changes. Inspect the resulting diff file by file and run the validation that matches the changed behavior.

PowerShell is appropriate for repeatable local diagnostics, validation, evidence capture, repository inspection, and controlled operational commands. Scripts must fail clearly, avoid hidden destructive behavior, and preserve reproducibility.

## 11. Pull-request closeout

Every pull request must identify:

- purpose and bounded scope;
- files changed and intentionally excluded;
- validation performed;
- known failures or limitations;
- independent-review status;
- rollback approach where applicable.

Human owners retain product, architecture, implementation, approval, security, and release accountability. Repository account attribution is not a substitute for a verified contributor record.

## 12. Handoff verification

A successor must be able to complete these steps from a clean clone without undocumented local assumptions. Before ownership transfer, independently verify setup, tests, deployment access, rollback, recovery, secrets access, and administrative control.

This guide does not certify pilot, production, compliance, or release approval. Use `docs/CURRENT_RELEASE_STATUS.md` for current release authority.
