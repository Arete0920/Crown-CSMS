param(
    [string]$Remote = "origin"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$branch = (git symbolic-ref --short HEAD).Trim()
if (-not $branch) {
    Write-Error "could not determine current branch"
    exit 1
}

$counts = (git rev-list --left-right --count "$Remote/$branch...$branch").Trim()
if (-not $counts) {
    Write-Error "could not compute branch parity counts"
    exit 1
}

$parts = $counts -split "\s+"
if ($parts.Length -ne 2) {
    Write-Error "unexpected parity output: $counts"
    exit 1
}

$behind = [int]$parts[0]
$ahead = [int]$parts[1]
Write-Output "[branch-parity] branch=$branch remote=$Remote ahead=$ahead behind=$behind"

if ($ahead -ne 0 -or $behind -ne 0) {
    Write-Error "branch parity check failed (ahead/behind must be 0/0)"
    exit 1
}

Write-Output "OK branch parity check passed"
exit 0
