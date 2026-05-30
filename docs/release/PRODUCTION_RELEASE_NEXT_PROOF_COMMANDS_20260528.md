# Production Release Next Proof Commands - 2026-05-28

## Local Verification Commands

```powershell
git status --short --branch
git fetch origin
git checkout main
git pull --ff-only origin main
python backend/manage.py check
python tools/verify_public_surface_policy.py
pytest -q tests/test_release_tenant_and_urls.py
pytest -q backend/billing/tests/test_billing_summary_api.py
pytest -q backend/tests/test_golden_path.py
```

## Frontend Verification If Present

```powershell
cd frontend/dashboards
npm ci
npm run test --if-present
cd ../..
```

## GitHub Verification Commands If gh Is Available

```powershell
gh run list --branch main --limit 10
gh workflow list
gh run view --log
```

## Safety Rule

Do not run deployment commands from this checklist. This document is for proof capture only.
