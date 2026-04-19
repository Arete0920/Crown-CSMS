$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$wfRoot = Join-Path $repoRoot ".github\workflows"
$base = Join-Path $repoRoot "audit-artifacts\workflow-permissions-verify"
New-Item -ItemType Directory -Force -Path $base | Out-Null

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$out = Join-Path $base ("verify_" + $ts + ".txt")

function Has-TopLevelPermissions {
    param([string[]]$Lines)
    foreach ($line in $Lines) {
        if ($line -match '^(permissions)\s*:\s*$') { return $true }
        if ($line -match '^\S' -and $line -notmatch '^(name|on|run-name|env|defaults|concurrency|jobs)\s*:') {
            break
        }
    }
    return $false
}

"=== VERIFY WORKFLOW PERMISSIONS ===" | Set-Content $out -Encoding utf8
Get-ChildItem $wfRoot -File | Where-Object { $_.Extension -in ".yml", ".yaml" } | Sort-Object Name | ForEach-Object {
    $lines = [System.IO.File]::ReadAllLines($_.FullName)
    $ok = Has-TopLevelPermissions -Lines $lines
    "{0} :: permissions={1}" -f $_.Name, $ok | Add-Content $out -Encoding utf8
}

Write-Host "Done: $out"
code $out
