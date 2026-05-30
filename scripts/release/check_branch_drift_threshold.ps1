param(
    [string]$TargetRef = "origin/main",
    [int]$MaxAhead = 25,
    [int]$MaxBehind = 25
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$counts = (git rev-list --left-right --count "$TargetRef...HEAD").Trim()
if (-not $counts) {
    Write-Error "could not compute drift counts"
    exit 1
}

$parts = $counts -split "\s+"
if ($parts.Length -ne 2) {
    Write-Error "unexpected drift output: $counts"
    exit 1
}

$behind = [int]$parts[0]
$ahead = [int]$parts[1]
Write-Output "[branch-drift] target=$TargetRef ahead=$ahead behind=$behind maxAhead=$MaxAhead maxBehind=$MaxBehind"

$errors = @()
if ($ahead -gt $MaxAhead) { $errors += "ahead exceeds threshold" }
if ($behind -gt $MaxBehind) { $errors += "behind exceeds threshold" }

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Output "ERROR $_" }
    Write-Error "branch drift threshold check failed"
    exit 1
}

Write-Output "OK branch drift threshold check passed"
exit 0
