param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function New-Dir { param([string]$Path) New-Item -ItemType Directory -Force -Path $Path | Out-Null }
function Write-Utf8 { param([string]$Path, [string[]]$Lines) $Lines | Set-Content -Path $Path -Encoding UTF8 }
function Write-JsonFile { param([string]$Path, $Object) ($Object | ConvertTo-Json -Depth 12) | Set-Content -Path $Path -Encoding UTF8 }

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw "Not inside a git repository." }
Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\financial-controls\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\financial-controls\latest"
New-Dir $outDir
New-Dir $latestDir

$controls = @(
    "invoice_tenant_scope",
    "posted_invoice_immutability",
    "adjustment_audit_trail",
    "payment_reconciliation",
    "duplicate_payment_detection",
    "refund_permission_audit",
    "financial_aid_privacy",
    "financial_aid_change_audit",
    "family_statement_reconciliation",
    "finance_export_logging",
    "support_finance_access_restriction",
    "payment_sandbox_live_separation",
    "webhook_signature_validation",
    "year_end_ledger_integrity",
    "live_financial_dashboard_sources"
)

$scanRoots = @("backend", "frontend", "docs", "scripts") | ForEach-Object { Join-Path $repoRoot $_ } | Where-Object { Test-Path $_ }
$allFiles = @()
foreach ($root in $scanRoots) {
    $allFiles += Get-ChildItem $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(py|ps1|js|jsx|ts|tsx|md|json|csv)$" }
}

$rows = @()
foreach ($control in $controls) {
    $tokens = $control -split "_"
    $hits = @()
    foreach ($file in $allFiles) {
        $text = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
        $matchCount = 0
        foreach ($token in $tokens) {
            if ($file.Name -match $token -or $text -match $token) { $matchCount++ }
        }
        if ($matchCount -ge [Math]::Min(2, $tokens.Count)) { $hits += $file.FullName }
    }
    $rows += [pscustomobject]@{
        Control = $control
        EvidenceSignalCount = $hits.Count
        CompletionStatus = if ($hits.Count -gt 0) { "PROOF_REQUIRED" } else { "BLOCKED_MISSING_SIGNAL" }
    }
}

$failures = @($rows | Where-Object { $_.CompletionStatus -ne "PASS" })
$rows | Export-Csv -Path (Join-Path $outDir "10_control_results.csv") -NoTypeInformation -Encoding UTF8
$failures | Export-Csv -Path (Join-Path $outDir "20_financial_permission_failures.csv") -NoTypeInformation -Encoding UTF8
Write-Utf8 -Path (Join-Path $outDir "30_ledger_reconciliation.md") -Lines @(
    "# CROWN Ledger Reconciliation",
    "",
    "No live ledger reconciliation was executed by this static gate.",
    "A green result requires invoice/payment/credit/refund/statement reconciliation against tenant-scoped runtime data."
)

$summary = @(
    "# CROWN Financial Controls Gate",
    "",
    "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "- Branch: $((git branch --show-current).Trim())",
    "- Head: $((git rev-parse HEAD).Trim())",
    "- Controls: $($controls.Count)",
    "- Non-pass rows: $($failures.Count)",
    "",
    "REVIEW REQUIRED",
    "",
    "This gate intentionally fails until financial controls are proven through runtime tests and ledger reconciliation evidence."
)
Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    branch = (git branch --show-current).Trim()
    head = (git rev-parse HEAD).Trim()
    pass = $false
    control_count = $controls.Count
    non_pass_count = $failures.Count
    controls = $rows
}
Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $outDir '99_STATUS.json')"
exit 1
