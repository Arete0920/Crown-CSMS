param(
  [string]$OutputDir,
  [string]$BaseUrl = "http://127.0.0.1:8000",
  [string]$SwaggerPath = "/api/docs/",
  [string]$HealthPath = "/health/",
  [string]$IntegrityPath = "/api/integrity/"
)

$ErrorActionPreference = "Stop"

$nativePreferenceVar = Get-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue
$hadNativePreference = ($null -ne $nativePreferenceVar)
$oldNativePreference = if ($hadNativePreference) { [bool]$nativePreferenceVar.Value } else { $false }
if ($hadNativePreference) {
  $global:PSNativeCommandUseErrorActionPreference = $false
}

function Save-InvokeWeb {
  param(
    [string]$Url,
    [string]$OutFile
  )
  try {
    $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 20
    [pscustomobject]@{
      url    = $Url
      status = "PASS"
      code   = [int]$resp.StatusCode
      body   = $resp.Content
    } | ConvertTo-Json -Depth 5 | Out-File $OutFile -Encoding utf8
    return $true
  } catch {
    [pscustomobject]@{
      url    = $Url
      status = "FAIL"
      error  = $_.Exception.Message
    } | ConvertTo-Json -Depth 5 | Out-File $OutFile -Encoding utf8
    return $false
  }
}

$healthOk = Save-InvokeWeb -Url ($BaseUrl + $HealthPath) -OutFile (Join-Path $OutputDir "02_health.json")
$integrityOk = Save-InvokeWeb -Url ($BaseUrl + $IntegrityPath) -OutFile (Join-Path $OutputDir "02_integrity.json")
$swaggerOk = Save-InvokeWeb -Url ($BaseUrl + $SwaggerPath) -OutFile (Join-Path $OutputDir "02_swagger.json")

$deployCheck = Join-Path $OutputDir "02_django_check_deploy.txt"
$migrations = Join-Path $OutputDir "02_django_showmigrations.txt"

try {
  $oldErrorActionPreference = $ErrorActionPreference
  $ErrorActionPreference = "Continue"

  & python backend/manage.py check --deploy 2>&1 | Out-File $deployCheck -Encoding utf8
  if ($LASTEXITCODE -ne 0) {
    throw "manage.py check --deploy failed"
  }

  & python backend/manage.py showmigrations 2>&1 | Out-File $migrations -Encoding utf8
  if ($LASTEXITCODE -ne 0) {
    throw "manage.py showmigrations failed"
  }

  $ErrorActionPreference = $oldErrorActionPreference

if (Test-Path "scripts/release/phase4_backend_verification_and_django_proof.ps1") {
  powershell -ExecutionPolicy Bypass -File "scripts/release/phase4_backend_verification_and_django_proof.ps1"
}
if (Test-Path "scripts/release/phase5_module_proof_matrix.ps1") {
  powershell -ExecutionPolicy Bypass -File "scripts/release/phase5_module_proof_matrix.ps1"
}
if (Test-Path "scripts/release/phase8_frontend_and_dashboard_proof.ps1") {
  powershell -ExecutionPolicy Bypass -File "scripts/release/phase8_frontend_and_dashboard_proof.ps1"
}

$summary = [pscustomobject]@{
  health_ok    = $healthOk
  integrity_ok = $integrityOk
  swagger_ok   = $swaggerOk
  deploy_check = $deployCheck
  migrations   = $migrations
}
$summary | ConvertTo-Json -Depth 4 | Out-File (Join-Path $OutputDir "02_backend_runtime_summary.json") -Encoding utf8

  if (-not ($healthOk -and $integrityOk -and $swaggerOk)) {
    throw "One or more runtime endpoints failed."
  }
} finally {
  $ErrorActionPreference = "Stop"
  if ($hadNativePreference) {
    $global:PSNativeCommandUseErrorActionPreference = $oldNativePreference
  }
}
