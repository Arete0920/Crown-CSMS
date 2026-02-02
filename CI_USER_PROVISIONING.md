# CI User Provisioning for DEV

## ⚠️ PREREQUISITE: This MUST be done before DEV smoke tests work

The `ci-golden@crown-demo.local` user must be pre-created on DEV. Without this user, golden path smoke tests fail with:

```
"No active account found with the given credentials"
```

## Problem
GitHub Actions secrets mechanism corrupts or truncates values when passed to workflows (likely a platform bug). The original ops provisioning endpoint approach doesn't work due to this corruption.

## Solution
The `ci-golden@crown-demo.local` user must be pre-created on DEV before running smoke tests.

### Manual Provisioning (One-time)

#### ✅ Option 1: Via Azure Portal SSH (Recommended & Easiest)
1. Go to [Azure Portal](https://portal.azure.com)
2. Search for → **crown-api-dev** (App Service)
3. Left sidebar → **SSH**
4. Click **"Go"** (opens SSH terminal in browser)
5. Run these commands:

```bash
cd /home/site/wwwroot/backend
python manage.py shell
```

6. Inside the Django shell, paste:

```python
from django.contrib.auth.models import User
user, created = User.objects.get_or_create(
    username='ci-golden@crown-demo.local',
    defaults={'email': 'ci@crown-demo.local', 'first_name': 'CI', 'last_name': 'Golden'}
)
user.set_password('Temp123!@#GoldenPath')
user.save()
print(f"✅ User created: {user.username}, id={user.id}")
exit()
```

7. Verify with:
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
u = User.objects.get(username='ci-golden@crown-demo.local')
print(f'✅ User exists: {u.username}')
"
```

#### Option 2: Via PowerShell from Local Machine (Requires SSH Keys)
```powershell
# Get the dev app service name and SSH endpoint (from Azure Portal)
# Then:
ssh <user@domain>
# Follow steps 5-7 above
```

#### Option 3: Via Kudu Console (Advanced)
1. Navigate to `crown-api-dev` → **Development Tools** → **Advanced Tools (Kudu)**
2. Click **"Debug console"** → **PowerShell**
3. Navigate: `cd D:\home\site\wwwroot\backend`
4. Run: `python manage.py shell` and paste the Python code from Option 1

### Verification
After provisioning, test the smoke workflow:
```powershell
gh workflow run "DEV Smoke - Golden Path" -f skip_seed=true
Start-Sleep 240
gh run list --workflow "dev-smoke.yml" --json status,conclusion --limit 1 | ConvertFrom-Json
```

Expected output:
```
status     conclusion
------     ----------
completed  success
```

If it still fails with auth error, the user doesn't exist. Go back to SSH and re-run the creation commands.

## How to Prevent This in the Future

1. **Pre-populate test users at deployment time** - use App Service startup scripts or migration commands
2. **Never rely on GitHub Actions secrets for ops credentials** - they're not designed for large values
3. **Use short, static secrets** (< 32 chars) for any remote ops endpoints
4. **Consider a dedicated provisioning workflow** that runs as a manual GitHub Actions step

## Related Issues
- GitHub Actions secret truncation: Reported to GitHub Support
- Ops endpoint code: [backend/crown_api/ops_views.py](backend/crown_api/ops_views.py) (currently disabled)
- Smoke workflow: [.github/workflows/dev-smoke.yml](.github/workflows/dev-smoke.yml)
- CI jobs (passing): [.github/workflows/ci.yml](.github/workflows/ci.yml) ✅
