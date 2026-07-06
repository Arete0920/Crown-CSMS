param(
    [string]$RepoRoot = "C:/Users/JMega/OneDrive/Desktop/Crown2026_deploypr"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location $RepoRoot

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $RepoRoot "audit-artifacts/runtime-release-closure/20260418_070051"
if (!(Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

$outFile = Join-Path $outDir "runner_recovery_rerun_pack_$stamp.txt"

function Write-Section([string]$title) {
    "`n=== $title ===" | Out-File -FilePath $outFile -Append -Encoding utf8
}

Write-Section "RERUN REQUESTS"
gh run rerun 26676524314 | Out-File -FilePath $outFile -Append -Encoding utf8
gh run rerun 26676520864 | Out-File -FilePath $outFile -Append -Encoding utf8
gh run rerun 26676516965 | Out-File -FilePath $outFile -Append -Encoding utf8

Write-Section "RUN SNAPSHOT"
gh run view 26676524314 --json databaseId,status,conclusion,updatedAt,jobs,url | Out-File -FilePath $outFile -Append -Encoding utf8
gh run view 26676520864 --json databaseId,status,conclusion,updatedAt,jobs,url | Out-File -FilePath $outFile -Append -Encoding utf8
gh run view 26676516965 --json databaseId,status,conclusion,updatedAt,jobs,url | Out-File -FilePath $outFile -Append -Encoding utf8

Write-Section "PR CHECK SNAPSHOT"
gh pr checks 869 --json name,state,workflow,bucket,link | Out-File -FilePath $outFile -Append -Encoding utf8
gh pr checks 870 --json name,state,workflow,bucket,link | Out-File -FilePath $outFile -Append -Encoding utf8

Write-Section "DONE"
"artifact=$outFile" | Out-File -FilePath $outFile -Append -Encoding utf8
Write-Output "artifact=$outFile"
