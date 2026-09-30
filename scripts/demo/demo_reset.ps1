#Requires -Version 5.1
$ErrorActionPreference="Stop"

$REPO="$env:USERPROFILE\OneDrive\Desktop\Crown2026"

Write-Host "`n=== DEMO AUTH RESET ===" -ForegroundColor Cyan
Write-Host "Ensuring deterministic demo credentials exist in backend...`n"

cd "$REPO\backend"
python manage.py seed_demo_auth

Write-Host ""
Write-Host "=== DEMO CREDENTIALS (DETERMINISTIC) ===" -ForegroundColor Green
Write-Host "School ID : 19801b59-8c05-4c84-9312-5d792e4e839d"
Write-Host ""
Write-Host "Real Login Page:"
Write-Host "  Username : admin"
Write-Host "  Password : supplied through CROWN_DEMO_PASSWORD"
Write-Host ""
Write-Host "Dev JWT Widget / API Tests:"
Write-Host "  Username : head@crown-demo.local"
Write-Host "  Password : supplied through CROWN_DEMO_PASSWORD"
Write-Host ""
Write-Host "Demo Mode Settings (backend .env):"
Write-Host "  CROWN_DEMO_MODE     = true"
Write-Host "  CROWN_DEMO_KEY      = CrownDemoKey!2026"
Write-Host "  CROWN_DEMO_SCHOOL_ID= 19801b59-8c05-4c84-9312-5d792e4e839d"
Write-Host ""
Write-Host "Frontend .env.local:"
Write-Host "  VITE_DEMO_KEY       = CrownDemoKey!2026"
Write-Host ""
Write-Host "API Base  : http://127.0.0.1:8000"
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Set backend env vars: CROWN_DEMO_MODE=true, CROWN_DEMO_KEY=CrownDemoKey!2026"
Write-Host "  2. Restart backend server"
Write-Host "  3. F12 → Application → Clear site data"
Write-Host "  4. Ctrl+Shift+R (hard refresh)"
Write-Host "  5. Click 'Demo Login' button (no password typing)"
