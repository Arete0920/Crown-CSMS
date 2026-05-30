# Production Release Verification Commands - 2026-05-29

## Local main sync

```powershell
Set-Location "C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr"

git status --short --branch
git fetch origin
git checkout main
git pull --ff-only origin main
git status --short --branch
```

## Backend checks

```powershell
python backend/manage.py check
python backend/manage.py showmigrations
python tools/verify_public_surface_policy.py
pytest -q tests/test_release_tenant_and_urls.py
pytest -q backend/billing/tests/test_billing_summary_api.py
pytest -q backend/tests/test_golden_path.py
```

## Frontend checks

```powershell
Set-Location "C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards"

npm ci
npm run test --if-present

Set-Location "C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr"
```

## GitHub hosted evidence

```powershell
gh run list --branch main --limit 10
gh workflow list
```

## Do not proceed if

- git pull is not fast-forward
- working tree is dirty
- any test fails
- hosted gates are not green
- live smoke is not green
