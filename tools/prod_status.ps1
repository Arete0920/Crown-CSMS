$ErrorActionPreference = "Stop"
$env:GH_PAGER = "cat"
$env:NO_COLOR = "1"

Write-Host "Latest deploy-prod.yml runs:" -ForegroundColor Cyan
gh run list --workflow=deploy-prod.yml --repo Arete0920/Crown-CSMS --limit 5

Write-Host ""
Write-Host "Latest prod-deploy tags:" -ForegroundColor Cyan
git fetch --tags | Out-Null
git tag --list "prod-deploy-*" | Sort-Object | Select-Object -Last 10

Write-Host ""
Write-Host "Main HEAD:" -ForegroundColor Cyan
git --no-pager log --oneline -1
