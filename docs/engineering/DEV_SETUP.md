# CROWN Engineering Setup

**Status:** Canonical  
**Purpose:** Tool-neutral setup and controlled execution

## Repository

```bash
git clone https://github.com/tcmegahan/Crown2026.git
cd Crown2026
```

Work from one isolated branch for one coherent outcome. Do not commit directly to `main`.

## Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
python backend/manage.py check
pytest backend -m "not integration and not slow"
```

Windows PowerShell may activate `.venv\Scripts\Activate.ps1`.

## Frontend

```bash
cd frontend/dashboards
npm ci
npm run lint
npm run test:unit
npm run test:contracts
npm run test:release:a11y
npm run build
```

## Local runtime

```bash
python backend/manage.py runserver 127.0.0.1:8000 --noreload
cd frontend/dashboards
npm run dev -- --host 127.0.0.1 --port 3000
```

Use placeholders or approved development values only. Never commit secrets, production data, private certificates, tenant credentials, or payment credentials.

## Change workflow

1. Read current GitHub state and controlling authority.
2. Record base SHA, objective, allowed files, validation, and rollback.
3. Use one branch and one pull request for the coherent outcome.
4. Keep related fixes found during validation in that pull request.
5. Run focused validation, then applicable broad checks.
6. Inspect the final diff.
7. Resolve actionable findings.
8. Merge only after the exact head satisfies policy.
9. Deploy only through approved workflows.
10. Capture exact deployed identity and runtime evidence when applicable.

Payment processing remains disabled until a provider is selected, contracted, implemented, and certified.
