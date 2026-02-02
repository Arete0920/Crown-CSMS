# CI User Provisioning for DEV

## Problem
GitHub Actions secrets mechanism appears to corrupt or truncate values > 1 character when passed to workflows. This prevents the ops provisioning endpoint from authenticating properly (403 Forbidden).

## Solution
The `ci-golden@crown-demo.local` user must be pre-created on DEV before running smoke tests.

### Manual Provisioning (One-time)

#### Option 1: Via Azure Portal SSH (Recommended)
1. Navigate to `crown-api-dev` App Service in Azure Portal
2. Click "SSH" → "Open"
3. Run:
   ```bash
   cd /home/site/wwwroot
   python manage.py shell << EOF
   from django.contrib.auth.models import User
   user, _ = User.objects.get_or_create(
       username='ci-golden@crown-demo.local',
       defaults={'email': 'ci@crown-demo.local', 'first_name': 'CI', 'last_name': 'Golden'}
   )
   user.set_password('Temp123!@#GoldenPath')
   user.save()
   print(f"✅ User created/updated: {user.username}")
   EOF
   ```

#### Option 2: Via Kudu Console
1. Navigate to `crown-api-dev` → Development Tools → Advanced Tools (Kudu)
2. Click "Debug console" → PowerShell
3. Navigate to `D:\home\site\wwwroot\backend`
4. Run the provisioning script:
   ```powershell
   python manage.py shell
   # Then paste the commands from Option 1
   ```

#### Option 3: Via GitHub Actions Workflow
Manually trigger the CI workflow with provisioning enabled:
1. Go to Actions → "Provision CI User (DEV)"
2. Click "Run workflow" → "Run workflow"
3. Wait for completion

### Verification
After provisioning, test the smoke workflow:
```bash
gh workflow run "DEV Smoke - Golden Path" \
  --ref main \
  --input skip_seed=true
```

Check logs:
```bash
gh run list --workflow "dev-smoke.yml" -L 1 | head -1 | awk '{print $1}' | xargs -I {} gh run view {} --log
```

## How to Prevent This in the Future

1. **Never pass large secrets directly to workflows** - use the GitHub Secrets API instead
2. **Use hardcoded, short secrets** for ops endpoints (< 32 chars)
3. **Pre-populate test users** at deployment time (during App Service startup)
4. **Consider rotating the secret monthly** to keep hygiene

## Related Issues
- GitHub Actions secret truncation: Filed investigation
- Ops endpoint code: `backend/crown_api/ops_views.py`
- Smoke workflow: `.github/workflows/dev-smoke.yml`
