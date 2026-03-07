# api_probe.ps1 - Role-based API probe (PowerShell 5.1 safe)
param(
  [Parameter(Mandatory=$true)][string]$ApiBase,
  [string]$SchoolId = '',
  [string]$TenantHeader = 'X-School-Id',
  [string]$OutDir = '.'
)

Set-StrictMode -Off
$ErrorActionPreference = 'Continue'

function Get-Token {
  param([string]$Email, [string]$Pass)
  $loginBody = '{"email":"' + $Email + '","password":"' + $Pass + '"}'
  $bodyFile = [System.IO.Path]::GetTempFileName()
  [System.IO.File]::WriteAllText($bodyFile, $loginBody)
  $tmp = [System.IO.Path]::GetTempFileName()
  $code = [int](& curl.exe -s -o $tmp -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d "@$bodyFile" ($ApiBase + '/api/auth/login/'))
  Remove-Item $bodyFile -ErrorAction SilentlyContinue
  if ($code -ne 200) { Remove-Item $tmp -ErrorAction SilentlyContinue; return $null }
  $raw = Get-Content $tmp -Raw -Encoding UTF8
  Remove-Item $tmp -ErrorAction SilentlyContinue
  try { return ($raw | ConvertFrom-Json).access } catch { return $null }
}

function Probe-Endpoint {
  param([string]$Token, [string]$Path, [string[]]$RequireKeys)
  $hdr = @('-H', ('Authorization: Bearer ' + $Token))
  if ($SchoolId) { $hdr += @('-H', ($TenantHeader + ': ' + $SchoolId)) }
  $tmp = [System.IO.Path]::GetTempFileName()
  $code = [int](& curl.exe -s -o $tmp -w '%{http_code}' @hdr ($ApiBase + $Path))
  $body = Get-Content $tmp -Raw -Encoding UTF8
  Remove-Item $tmp -ErrorAction SilentlyContinue
  if ($code -ne 200) {
    $snip = if ($body.Length -gt 240) { $body.Substring(0,240) } else { $body }
    return @{ ok=$false; code=$code; detail=$snip }
  }
  if ($RequireKeys -and $RequireKeys.Count -gt 0) {
    try {
      $j = $body | ConvertFrom-Json
      $miss = foreach ($k in $RequireKeys) { if (-not ($j.PSObject.Properties.Name -contains $k)) { $k } }
      if ($miss) { return @{ ok=$false; code=$code; detail=('Missing keys: ' + ($miss -join ', ')) } }
    } catch {
      return @{ ok=$false; code=$code; detail=('JSON parse failed: ' + $_.Exception.Message) }
    }
  }
  return @{ ok=$true; code=$code; detail='HTTP 200 + schema OK' }
}

$results = [System.Collections.Generic.List[object]]::new()
$fail = 0; $warn = 0; $pass = 0

# Role credentials come from env vars
$roleMap = @(
  @{ slug='admin';     email=$env:CROWN_ROLE_ADMIN_EMAIL;     pass=$env:CROWN_ROLE_ADMIN_PASS }
  @{ slug='teacher';   email=$env:CROWN_ROLE_TEACHER_EMAIL;   pass=$env:CROWN_ROLE_TEACHER_PASS }
  @{ slug='parent';    email=$env:CROWN_ROLE_PARENT_EMAIL;    pass=$env:CROWN_ROLE_PARENT_PASS }
  @{ slug='student';   email=$env:CROWN_ROLE_STUDENT_EMAIL;   pass=$env:CROWN_ROLE_STUDENT_PASS }
  @{ slug='finance';   email=$env:CROWN_ROLE_FINANCE_EMAIL;   pass=$env:CROWN_ROLE_FINANCE_PASS }
  @{ slug='registrar'; email=$env:CROWN_ROLE_REGISTRAR_EMAIL; pass=$env:CROWN_ROLE_REGISTRAR_PASS }
)

# Endpoints validated for each authenticated role
$endpoints = @(
  @{ path='/api/v1/nav/';                keys=@('groups') }
  @{ path='/api/admissions/summary/';    keys=@('counts') }
  @{ path='/api/financial-aid/summary/'; keys=@('counts') }
  @{ path='/api/v1/finance/summary/';    keys=@('ok') }
)

foreach ($r in $roleMap) {
  if (-not $r.email -or -not $r.pass) {
    $warn++
    $results.Add([pscustomobject]@{ level='WARN'; role=$r.slug; check='login'; detail='Missing env creds; skipped' })
    continue
  }
  Write-Host "  Probing role: $($r.slug)"
  $token = Get-Token $r.email $r.pass
  if (-not $token) {
    $fail++
    $results.Add([pscustomobject]@{ level='FAIL'; role=$r.slug; check='login'; detail='Login failed (non-200 or no token)' })
    continue
  }
  $pass++
  $results.Add([pscustomobject]@{ level='PASS'; role=$r.slug; check='login'; detail='Token issued OK' })

  foreach ($ep in $endpoints) {
    $res = Probe-Endpoint $token $ep.path $ep.keys
    $slug = $ep.path.Trim('/')
    if ($res.ok) {
      $pass++
      $results.Add([pscustomobject]@{ level='PASS'; role=$r.slug; check=$slug; detail=$res.detail })
    } else {
      $fail++
      $results.Add([pscustomobject]@{ level='FAIL'; role=$r.slug; check=$slug; detail="HTTP $($res.code) -- $($res.detail)" })
    }
  }
}

$outJson = Join-Path $OutDir 'api_probe_results.json'
$results | ConvertTo-Json -Depth 6 | Out-File $outJson -Encoding ascii
Write-Host "Results: $outJson"
Write-Host "Summary: PASS=$pass WARN=$warn FAIL=$fail"

if ($fail -gt 0) { exit 2 } elseif ($warn -gt 0) { exit 1 } else { exit 0 }
