$files = @(
  "docs\audit\README.md",
  "docs\audit\inventories\MASTER_PLATFORM_INVENTORY.csv",
  "docs\audit\inventories\CORE_INVENTORY.csv",
  "docs\audit\inventories\MODULE_INVENTORY.csv",
  "docs\audit\inventories\ADDON_INVENTORY.csv",
  "docs\audit\inventories\DASHBOARD_WIZARD_PAGE_INVENTORY.csv",
  "docs\audit\inventories\API_ROUTE_CONTRACT_INVENTORY.csv",
  "docs\audit\inventories\MODEL_SERVICE_INVENTORY.csv",
  "docs\audit\inventories\TEST_CI_DOC_INVENTORY.csv",
  "docs\audit\scans\TODO_SCAN.csv",
  "docs\audit\scans\PLACEHOLDER_SCAN.csv",
  "docs\audit\scans\ROUTE_RISK_SCAN.csv",
  "docs\audit\scans\WORKFLOW_RISK_SCAN.csv",
  "docs\audit\evidence\PROOF_SUMMARY.csv",
  "docs\audit\reports\MODULE_COMPLETION_MATRIX.csv",
  "docs\audit\reports\KEEP_REWRITE_DROP_MATRIX.csv",
  "docs\audit\reports\DASHBOARD_WIZARD_STATUS.csv",
  "docs\audit\reports\FINAL_AUDIT_SCORECARD.md",
  "docs\audit\reports\FINAL_EXECUTIVE_AUDIT_SUMMARY.md"
)
foreach ($f in $files) {
  if (Test-Path $f) { code $f }
}
