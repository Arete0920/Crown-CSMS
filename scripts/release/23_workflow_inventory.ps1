$ErrorActionPreference = "Stop"

$base = "audit-artifacts\release-manifest"
New-Item -ItemType Directory -Force -Path $base | Out-Null

$canonical = @(
  "backend-gate",
  "frontend-gate",
  "contract-gate",
  "secret-scan",
  "CodeQL",
  "dependency-audit",
  "release-verify",
  "deploy-prod",
  "prod-health-watch",
  "demo-verify",
  "rc-probe",
  "proof-ceremony"
)

$result = @()
Get-ChildItem .github\workflows -File -Include *.yml,*.yaml -ErrorAction SilentlyContinue | ForEach-Object {
  $name = $_.BaseName
  $result += [pscustomobject]@{
    workflow = $_.Name
    base = $name
    canonical = ($canonical -contains $name)
  }
}

$result | Export-Csv "$base\08_workflow_inventory.csv" -NoTypeInformation
Write-Host "Workflow inventory written."