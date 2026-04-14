$files = @(
  "docs\audit\reports\EXEC_BOARD_REPORT.md",
  "docs\audit\reports\BOARD_TOP_25_BLOCKERS.csv",
  "docs\audit\reports\MODULE_COMPLETION_MATRIX.csv",
  "docs\audit\reports\KEEP_REWRITE_DROP_MATRIX.csv",
  "docs\audit\reports\DASHBOARD_WIZARD_STATUS.csv",
  "docs\audit\evidence\PROOF_SUMMARY.csv",
  "docs\audit\scans\TODO_SCAN.csv",
  "docs\audit\scans\PLACEHOLDER_SCAN.csv",
  "docs\audit\scans\ROUTE_RISK_SCAN.csv",
  "docs\audit\scans\WORKFLOW_RISK_SCAN.csv"
)
foreach ($f in $files) {
  if (Test-Path $f) { code $f }
}
