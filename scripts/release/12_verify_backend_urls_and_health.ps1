$ErrorActionPreference = "Stop"
$base = "audit-artifacts\verify-high-risk"
New-Item -ItemType Directory -Force -Path $base | Out-Null
$BaseUrl = "http://127.0.0.1:8000"

"=== HEALTH ===" | Out-File "$base\06_health_verify.txt"
try {
  Invoke-RestMethod -Uri "$BaseUrl/api/health/" -Method Get -TimeoutSec 20 |
    ConvertTo-Json -Depth 10 | Add-Content "$base\06_health_verify.txt"
} catch {
  $_ | Out-String | Add-Content "$base\06_health_verify.txt"
}

"=== INTEGRITY ===" | Out-File "$base\07_integrity_verify.txt"
try {
  Invoke-RestMethod -Uri "$BaseUrl/api/integrity/" -Method Get -TimeoutSec 20 |
    ConvertTo-Json -Depth 10 | Add-Content "$base\07_integrity_verify.txt"
} catch {
  $_ | Out-String | Add-Content "$base\07_integrity_verify.txt"
}

"=== URL SEARCH ===" | Out-File "$base\08_url_search.txt"
$allFiles = Get-ChildItem -Recurse -File backend 2>$null | ForEach-Object FullName
if (-not $allFiles) { $allFiles = Get-ChildItem -Recurse -File | ForEach-Object FullName }
$patterns = @("/api/health/","/api/integrity/","urlpatterns","include(","path(")
foreach ($p in $patterns) {
  "===== $p =====" | Add-Content "$base\08_url_search.txt"
  Select-String -Path $allFiles -Pattern $p -SimpleMatch 2>$null |
    ForEach-Object { "{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line.Trim() } |
    Add-Content "$base\08_url_search.txt"
}

Write-Host "Done: $base"