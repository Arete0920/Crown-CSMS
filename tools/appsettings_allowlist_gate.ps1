Param(
  [Parameter(Mandatory=$true)]
  [string] $AppSettingsJsonPath,

  [Parameter(Mandatory=$true)]
  [string[]] $AllowedKeys
)

if (!(Test-Path $AppSettingsJsonPath)) {
  Write-Error "App settings JSON not found at: $AppSettingsJsonPath"
  exit 2
}

$raw = Get-Content $AppSettingsJsonPath -Raw
if ([string]::IsNullOrWhiteSpace($raw)) {
  Write-Error "App settings JSON is empty: $AppSettingsJsonPath"
  exit 2
}

# Accept either:
# 1) {"KEY":"VALUE",...}
# 2) [{"name":"KEY","value":"VALUE"}, ...]
$data = $raw | ConvertFrom-Json

$keys = @()
if ($data -is [System.Collections.IEnumerable] -and $data.Count -gt 0 -and $data[0].PSObject.Properties.Name -contains "name") {
  $keys = $data | ForEach-Object { $_.name }
} else {
  $keys = $data.PSObject.Properties.Name
}

$keys = $keys | Sort-Object -Unique
$allowed = $AllowedKeys | Sort-Object -Unique

$forbidden = $keys | Where-Object { $_ -notin $allowed }

Write-Host "=== App Settings Gate ==="
Write-Host "Allowed keys:"
$allowed | ForEach-Object { Write-Host "  + $_" }

Write-Host "Keys requested by workflow:"
$keys | ForEach-Object { Write-Host "  * $_" }

if ($forbidden.Count -gt 0) {
  Write-Host ""
  Write-Error "FORBIDDEN app settings detected:"
  $forbidden | ForEach-Object { Write-Host "  - $_" }
  Write-Host ""
  Write-Error "Refusing to apply app settings. Fix workflow or allowlist."
  exit 3
}

Write-Host "Gate passed."
exit 0