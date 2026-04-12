$ErrorActionPreference = "Stop"
$base = "audit-artifacts\verify-high-risk"
New-Item -ItemType Directory -Force -Path $base | Out-Null

$wf = Get-ChildItem -Recurse -File ".github\workflows" -Include *.yml,*.yaml 2>$null

"=== WORKFLOW LIST ===" | Out-File "$base\09_workflow_list.txt"
$wf | Select-Object FullName | Format-Table -AutoSize | Out-String | Add-Content "$base\09_workflow_list.txt"

"=== JOB-LEVEL IF / HIGH-RISK TOKENS ===" | Out-File "$base\10_workflow_if_hits.txt"
$patterns = @(
  "if:",
  "workflow_dispatch:",
  "pull_request:",
  "push:",
  "schedule:",
  "deploy-prod",
  "proof-ceremony",
  "secret-scan",
  "dependency-audit",
  "release-verify"
)
foreach ($p in $patterns) {
  "===== $p =====" | Add-Content "$base\10_workflow_if_hits.txt"
  Select-String -Path ($wf.FullName) -Pattern $p -SimpleMatch 2>$null |
    ForEach-Object { "{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line.Trim() } |
    Add-Content "$base\10_workflow_if_hits.txt"
}

"=== RECENT COMMITS TOUCHING WORKFLOWS ===" | Out-File "$base\11_workflow_git_history.txt"
git log --oneline -- .github/workflows 2>&1 | Add-Content "$base\11_workflow_git_history.txt"

Write-Host "Done: $base"