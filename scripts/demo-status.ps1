$ErrorActionPreference="Stop"
$API="https://crown-api-dev.azurewebsites.net"
$SCHOOL_ID="a5351136-98fe-4d48-add0-fa8f62d9ceff"
$USER="head@crown-demo.local"

# Password must be supplied through the environment before running this script.
if (-not $env:CROWN_PASSWORD) { throw "CROWN_PASSWORD environment variable is required." }
$PASS=$env:CROWN_PASSWORD

$body = @{ username=$USER; password=$PASS } | ConvertTo-Json -Compress
$token = (Invoke-RestMethod -Uri "$API/api/v1/auth/token/" -Method Post -ContentType "application/json" -Body $body).access

$headers = @{ Authorization="Bearer $token"; "X-School-Id"=$SCHOOL_ID }

$health = Invoke-RestMethod -Uri "$API/health" -Method Get
$adm = Invoke-RestMethod -Uri "$API/api/v1/admissions/summary/" -Headers $headers -Method Get

"health.status: $($health.status)"
"health.build_sha: $($health.build_sha)"
"admissions.total: $($adm.pipeline.total)"
"admissions.by_stage:"
$adm.pipeline.by_stage | ConvertTo-Json -Depth 5
