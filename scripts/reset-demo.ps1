# Direct API call to reset DEV demo (bypasses broken GitHub Actions dispatch)
$API = "https://crown-api-dev.azurewebsites.net"
$OPS = "mbnT3VPw+RoSgCbAuqfir/9CUT6D0JpB"
$SCHOOL_ID = "a5351136-98fe-4d48-add0-fa8f62d9ceff"

Write-Host "🔄 Resetting DEV demo..." -ForegroundColor Cyan

$response = curl.exe -sS "$API/api/v1/system/demo-reset/?verbosity=1" `
    -X POST `
    -H "X-Admin-Ops-Secret: $OPS" `
    -H "X-School-Id: $SCHOOL_ID" `
    -H "Content-Type: application/json" `
    -d "{}" | ConvertFrom-Json

if ($response.ok) {
    Write-Host "✅ Demo reset complete" -ForegroundColor Green
    Write-Host "   School: $($response.school_id)" -ForegroundColor Gray
    Write-Host "   Environment: $($response.env)" -ForegroundColor Gray
} else {
    Write-Host "❌ Reset failed" -ForegroundColor Red
    $response | ConvertTo-Json
}
