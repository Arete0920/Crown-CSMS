param(
  [Parameter(Mandatory=$true)]
  [string]$SchoolId
)

$ErrorActionPreference = "Stop"
$API="https://crown-api-dev.azurewebsites.net"

# Prompt for password securely (no env-var drama)
$PW = Read-Host "Password for head@crown-demo.local" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($PW)
$Plain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

$body = @{ username="head@crown-demo.local"; password=$Plain } | ConvertTo-Json -Compress
$token = (Invoke-RestMethod -Uri "$API/api/v1/auth/token/" -Method Post -ContentType "application/json" -Body $body).access

if (-not $token) { throw "Token acquisition failed." }

$headers = @{ Authorization="Bearer $token"; "X-School-Id"=$SchoolId }

# Health
$health = Invoke-RestMethod -Uri "$API/health" -Method Get
"Health OK: $(($health | ConvertTo-Json -Compress))" | Write-Host

# Admissions summary
$sum = Invoke-RestMethod -Uri "$API/api/v1/admissions/summary/" -Headers $headers
$by = $sum.pipeline.by_stage
$nonzero = @()
foreach ($k in $by.PSObject.Properties.Name) {
  if ([int]$by.$k -gt 0) { $nonzero += $k }
}
"Admissions total: $([int]$sum.pipeline.total)" | Write-Host
"Admissions nonzero stages: $(($nonzero -join ', '))" | Write-Host

if ($nonzero.Count -lt 3) {
  throw "FAIL: Admissions demo not diversified (need >=3 non-zero stages)."
}

"PASS: Demo looks good." | Write-Host
