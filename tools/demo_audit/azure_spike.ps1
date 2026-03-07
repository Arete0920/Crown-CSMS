param(
  [Parameter(Mandatory=$true)][string]$Url,
  [int]$Seconds = 60
)

Set-StrictMode -Off
$ErrorActionPreference = "Stop"

$start = Get-Date
$end = $start.AddSeconds($Seconds)
$bad = 0
$total = 0

Write-Host "Spike test: $Url ($Seconds seconds)"

while ((Get-Date) -lt $end) {
  $total++
  try {
    $code = & curl.exe -s -o NUL -w "%{http_code}" $Url
    $c = [int]$code
    $ts = (Get-Date).ToString("HH:mm:ss")
    Write-Host "$ts  HTTP $c"
    if ($c -eq 503 -or $c -eq 502 -or $c -eq 504 -or $c -eq 0) { $bad++ }
  } catch {
    $bad++
    Write-Host "ERR $($_.Exception.Message)"
  }
  Start-Sleep -Seconds 1
}

Write-Host "Spike summary: total=$total bad=$bad"
if ($bad -gt 0) { exit 2 } else { exit 0 }
