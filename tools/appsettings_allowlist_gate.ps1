Param(
  [Parameter(Mandatory=$true)]
  [string] $AppSettingsJsonPath,

  [Parameter(Mandatory=$false)]
  [string[]] $AllowedKeys,

  [Parameter(Mandatory=$false)]
  [string] $AllowedKeysFile,

  [Parameter(Mandatory=$false)]
  [string] $AllowedKeySet
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

$resolvedAllowed = @()
if ($AllowedKeys -and $AllowedKeys.Count -gt 0) {
  $resolvedAllowed += $AllowedKeys
}

if (![string]::IsNullOrWhiteSpace($AllowedKeysFile)) {
  if (!(Test-Path $AllowedKeysFile)) {
    Write-Error "Allowed keys file not found at: $AllowedKeysFile"
    exit 2
  }

  $hashFile = "$AllowedKeysFile.sha256"
  if (Test-Path $hashFile) {
    $expectedHash = (Get-Content $hashFile -Raw).Trim().ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($expectedHash)) {
      Write-Error "Allowed keys hash file is empty: $hashFile"
      exit 2
    }
    $actualHash = (Get-FileHash -Path $AllowedKeysFile -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $expectedHash) {
      Write-Error "Allowed keys file integrity check failed for $AllowedKeysFile"
      Write-Error "Expected SHA256: $expectedHash"
      Write-Error "Actual SHA256:   $actualHash"
      exit 3
    }
  }

  $allowRaw = Get-Content $AllowedKeysFile -Raw
  if ([string]::IsNullOrWhiteSpace($allowRaw)) {
    Write-Error "Allowed keys file is empty: $AllowedKeysFile"
    exit 2
  }

  $allowData = $allowRaw | ConvertFrom-Json
  if (![string]::IsNullOrWhiteSpace($AllowedKeySet)) {
    if (-not ($allowData.PSObject.Properties.Name -contains $AllowedKeySet)) {
      Write-Error "Allowed key set '$AllowedKeySet' not found in file: $AllowedKeysFile"
      exit 2
    }
    $resolvedAllowed += @($allowData.$AllowedKeySet)
  } else {
    if ($allowData -is [System.Collections.IEnumerable]) {
      $resolvedAllowed += @($allowData)
    } else {
      $resolvedAllowed += @($allowData.PSObject.Properties.Name)
    }
  }
}

if (-not $resolvedAllowed -or $resolvedAllowed.Count -eq 0) {
  Write-Error "No allowed keys provided. Use -AllowedKeys or -AllowedKeysFile (and optional -AllowedKeySet)."
  exit 2
}

$keys = $keys | Sort-Object -Unique
$allowed = $resolvedAllowed | Sort-Object -Unique

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
