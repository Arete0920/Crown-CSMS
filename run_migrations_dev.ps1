# Run migrations on Azure DEV webapp (crown-api-dev)

Write-Host "🔧 Setting RUN_MIGRATE=1 on crown-api-dev..."
az webapp config appsettings set -g crown-rg -n crown-api-dev --settings RUN_MIGRATE=1 | Out-Null

Write-Host "♻️  Restarting webapp..."
az webapp restart -g crown-rg -n crown-api-dev | Out-Null

Write-Host "⏳ Waiting for migrations to complete (60s)..."
Start-Sleep -Seconds 60

Write-Host "🩺 Testing health endpoint..."
$health = curl.exe -s "https://crown-api-dev.azurewebsites.net/api/health/"
Write-Host $health

Write-Host "🔧 Resetting RUN_MIGRATE=0..."
az webapp config appsettings set -g crown-rg -n crown-api-dev --settings RUN_MIGRATE=0 | Out-Null

Write-Host "♻️  Final restart..."
az webapp restart -g crown-rg -n crown-api-dev | Out-Null

Write-Host "✅ Migrations complete! Wait ~30s for app warmup, then re-run DEV Smoke."
