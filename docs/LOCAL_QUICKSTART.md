# Local Development Quick Start

**Purpose:** Get Crown2026 running locally with demo data for testing category weights and other academics features.

## Prerequisites

- Python 3.12+ installed
- PostgreSQL running (or use SQLite for quick demos)
- Node.js 18+ for frontend

## Backend Setup (5 minutes)

### 1. Install Dependencies
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# OR: source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Run Migrations
```powershell
python manage.py migrate
```

### 3. Seed Demo Data
Use the canonical demo school ID for consistency with Azure DEV:

```powershell
$SCHOOL_ID = "a5351136-98fe-4d48-add0-fa8f62d9ceff"

# Bootstrap golden path (creates school, admin user, sections, etc.)
python manage.py golden_path_bootstrap --school-id $SCHOOL_ID --force

# Seed gradebook data (grade entries for students)
python manage.py seed_gradebook_demo --school-id $SCHOOL_ID --per-section 5

# Seed category weights (Homework, Tests, Projects, Exams with percentages)
python manage.py seed_category_weights --school-id $SCHOOL_ID
```

### 4. Start Backend Server
```powershell
python manage.py runserver 127.0.0.1:8000
```

**Admin Credentials:**
- Username: `admin`
- Password: `Crown2026!`

**Test Backend:**
```powershell
curl http://127.0.0.1:8000/api/health/
# Should return: {"ok": true, "status": "ok", "build_sha": "local-dev"}
```

## Frontend Setup (3 minutes)

### 1. Install Dependencies
```powershell
cd frontend/dashboards
npm install
```

### 2. Start Dev Server
```powershell
npm run dev -- --port 3000
```

**Access Frontend:**
- URL: http://localhost:3000/
- Login with admin credentials above

## Test Category Weights Feature

### Via Frontend (Recommended):
1. Navigate to http://localhost:3000/category-weights
2. Select a section from dropdown
3. Edit category weights (should sum to 100%)
4. Click "Save Weights"

### Via API (For Testing):
```powershell
# Get token
$creds = @{username='admin';password='Crown2026!'} | ConvertTo-Json
$response = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/auth/token/' `
  -Method POST -Headers @{'Content-Type'='application/json'} -Body $creds
$token = $response.access

# List sections
curl.exe -s 'http://127.0.0.1:8000/api/v1/gradebook/sections/' `
  -H "Authorization: Bearer $token" | python -m json.tool

# Get categories for a section (replace <section_id>)
curl.exe -s 'http://127.0.0.1:8000/api/v1/academics/sections/<section_id>/categories/' `
  -H "Authorization: Bearer $token" | python -m json.tool
```

## Troubleshooting

### "No sections found"
**Cause:** Bootstrap didn't create sections with enrollments.  
**Fix:** Check that golden_path_bootstrap completed successfully. Look for sections in Django admin.

### "Weights don't sum to 100"
**Cause:** seed_category_weights creates 20% + 30% + 25% + 25% = 100% by default.  
**Fix:** This is expected! It's the MVP state. Use the UI to edit weights.

### "Admin login fails"
**Cause:** Bootstrap didn't run or password is wrong.  
**Fix:** 
```powershell
python manage.py shell
>>> from core.models import CustomUser
>>> admin = CustomUser.objects.get(username='admin')
>>> admin.set_password('Crown2026!')
>>> admin.save()
```

### Frontend can't connect to backend
**Cause:** CORS or backend not running.  
**Fix:** Ensure backend is running on port 8000. Check `crown_api/settings.py` has `CORS_ALLOWED_ORIGINS` including `http://localhost:3000`.

## Resetting Demo Data

To wipe and re-seed:

```powershell
$SCHOOL_ID = "a5351136-98fe-4d48-add0-fa8f62d9ceff"

# Wipe category weights
python manage.py seed_category_weights --school-id $SCHOOL_ID --wipe

# Wipe gradebook
python manage.py seed_gradebook_demo --school-id $SCHOOL_ID --wipe

# Re-run full bootstrap
python manage.py golden_path_bootstrap --school-id $SCHOOL_ID --force
python manage.py seed_gradebook_demo --school-id $SCHOOL_ID
python manage.py seed_category_weights --school-id $SCHOOL_ID
```

## What You Get

After following this guide:

- ✅ **School:** Crown Demo School (deterministic UUID)
- ✅ **Admin User:** admin / Crown2026!
- ✅ **Sections:** Multiple sections with enrollments
- ✅ **Students:** Demo students enrolled in sections
- ✅ **Grade Entries:** 5 assignments per section with realistic scores
- ✅ **Category Weights:** 4 categories (Homework 20%, Quizzes 30%, Projects 25%, Exams 25%)

## Next Steps

1. **Test Weighted Grading:** Edit category weights and verify transcript calculations change
2. **Test Permissions:** Create additional users with different roles (STAFF, DIRECTOR)
3. **Add More Data:** Use Django admin to create additional courses, sections, students

## Related Documentation

- [AZURE_DEV_APP_SETTINGS.md](./AZURE_DEV_APP_SETTINGS.md) - Azure deployment config
- [README_DIRECTOR_ACTIONS.md](../README_DIRECTOR_ACTIONS.md) - Director API usage
- [INTEGRATION_GUIDE.md](../INTEGRATION_GUIDE.md) - Frontend integration patterns
