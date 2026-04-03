# Run migrations and bootstrap on Azure webapp

Write-Host "Running migrations..."
az webapp config appsettings set -g crown-rg -n crown2026-api-dev --settings RUN_MIGRATE=1 | Out-Null
az webapp restart -g crown-rg -n crown2026-api-dev | Out-Null
Write-Host "Waiting for migrations to complete..."
Start-Sleep -Seconds 60

Write-Host "Testing health..."
$health = curl.exe -s "https://crown2026-api-dev.azurewebsites.net/health/"
Write-Host $health

Write-Host "Resetting RUN_MIGRATE to 0..."
az webapp config appsettings set -g crown-rg -n crown2026-api-dev --settings RUN_MIGRATE=0 | Out-Null

Write-Host "Running golden_path_bootstrap..."
az webapp config appsettings set -g crown-rg -n crown2026-api-dev --settings RUN_GOLDEN_PATH_BOOTSTRAP=1 | Out-Null
az webapp restart -g crown-rg -n crown2026-api-dev | Out-Null
Write-Host "Waiting for bootstrap to complete..."
Start-Sleep -Seconds 60

Write-Host "Testing households API..."
$jwt = curl.exe -s "https://crown2026-api-dev.azurewebsites.net/api/auth/token/" -X POST -H "Content-Type: application/json" -d '{\"username\":\"admin\",\"password\":\"Crown2026!\"}' | ConvertFrom-Json
$ACCESS = $jwt.access
$households = curl.exe -s -H "Authorization: Bearer $ACCESS" "https://crown2026-api-dev.azurewebsites.net/api/households/"
Write-Host $households

Write-Host "Resetting RUN_GOLDEN_PATH_BOOTSTRAP to 0..."
az webapp config appsettings set -g crown-rg -n crown2026-api-dev --settings RUN_GOLDEN_PATH_BOOTSTRAP=0 | Out-Null
az webapp restart -g crown-rg -n crown2026-api-dev | Out-Null

Write-Host "Done!"
