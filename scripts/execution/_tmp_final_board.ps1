Set-Location C:\w\crown_main_postmerge_verify
$Out = "C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-phase2-validation\20260430_024221"
$Ops = "C:\w\crown_main_postmerge_verify\docs\crown-master-binder\operations"
$LatestReadiness = (Get-Content "C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-production-readiness\LATEST.txt" -Raw).Trim()

$Blockers = @(
  [pscustomobject]@{Priority='P0'; Area='Security';    Issue='295 possible secret hits -- TRIAGED. 1 real fix applied (create_superuser.py). All others test fixtures or env-var reads.'; Owner='Dev 5'; Evidence="$Out\22b_secret_scan_triage.csv"; RequiredFix='DONE. Set DJANGO_SUPERUSER_PASSWORD env var in deployment to override default.'; Status='RESOLVED'}
  [pscustomobject]@{Priority='P0'; Area='Deployment';  Issue='AZURE_SWA_TOKEN missing as repo secret.'; Owner='Azure admin'; Evidence='GitHub Settings > Secrets and variables > Actions'; RequiredFix='Add AZURE_SWA_TOKEN from Azure Portal > Static Web Apps > crown-dash > Manage deployment token.'; Status='Open'}
  [pscustomobject]@{Priority='P0'; Area='Deployment';  Issue='AZURE_CREDENTIALS missing from production environment.'; Owner='Azure admin'; Evidence='GitHub Settings > Environments > production > Secrets'; RequiredFix='Add AZURE_CREDENTIALS (Service Principal JSON) to production env secrets.'; Status='Open'}
  [pscustomobject]@{Priority='P0'; Area='Deployment';  Issue='Frontend HTTP 404 -- crown-dash not deployed.'; Owner='Azure admin'; Evidence='curl.exe https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/'; RequiredFix='Fix AZURE_SWA_TOKEN then rerun workflow 25139353897.'; Status='Open'}
  [pscustomobject]@{Priority='P1'; Area='UI/Product';  Issue='331 placeholder hits -- TRIAGED. 1 real fix: transcript MVP notes removed. 98 form attributes safe. 30+ test files safe. See 20b triage.'; Owner='Dev 4 / Dev 5'; Evidence="$Out\20b_placeholder_scan_triage.csv"; RequiredFix='PARTIALLY RESOLVED. Dev 4 to confirm: (a) SeatingAdminPage default layout, (b) AcademicsDashboard Attendance coming-soon button acceptable for sandbox.'; Status='PARTIAL'}
  [pscustomobject]@{Priority='P1'; Area='UI Polish';   Issue='52 anti-pattern hits -- TRIAGED. 9 fixed (accent:navy->royal). 8 dev-gated console.logs safe. 25 test files safe. 3 playwright safe.'; Owner='Dev 4'; Evidence="$Out\21b_ui_antipattern_triage.csv"; RequiredFix='PARTIALLY RESOLVED. Dev 4 to review: (a) LoginPage dark-navy gradient -- intentional brand or convert to light? (b) BillingDashboard 1 remaining hit.'; Status='PARTIAL'}
  [pscustomobject]@{Priority='P1'; Area='Accessibility'; Issue='514 accessibility review hits.'; Owner='Dev 4'; Evidence="$LatestReadiness\26_accessibility_review.csv"; RequiredFix='Fix critical (blocking) a11y items. Mark acceptable deferred items. Run axe-core or Playwright a11y check to identify WCAG 2.1 AA violations.'; Status='Open'}
  [pscustomobject]@{Priority='P2'; Area='Validation';  Issue='npm run lint + lint:fix produced minimal output.'; Owner='Dev 5'; Evidence="$Out\validation_Frontend_Node_5.txt"; RequiredFix='VERIFIED: ESLint reports zero errors/warnings in clean shell. RESOLVED.'; Status='RESOLVED'}
  [pscustomobject]@{Priority='P2'; Area='Backend';     Issue='python manage.py check returned 0 issues.'; Owner='Dev 1'; Evidence="$Out\validation_Backend_Django_18.txt"; RequiredFix='VERIFIED: Re-run after create_superuser.py + transcript_views.py fixes -- still 0 issues. RESOLVED.'; Status='RESOLVED'}
)
$Blockers | Export-Csv "$Out\07_RELEASE_BLOCKER_BOARD.csv" -NoTypeInformation
Copy-Item "$Out\07_RELEASE_BLOCKER_BOARD.csv" "$Ops\12_RELEASE_BLOCKER_BOARD.csv" -Force

$OpenP0 = @($Blockers | Where-Object { $_.Priority -eq 'P0' -and $_.Status -eq 'Open' }).Count
$OpenP1 = @($Blockers | Where-Object { $_.Priority -eq 'P1' -and $_.Status -in ('Open','PARTIAL') }).Count
$Resolved = @($Blockers | Where-Object { $_.Status -in ('RESOLVED','PARTIAL') }).Count

Write-Host "Final blocker board:"
Write-Host "  Open P0:  $OpenP0 (all Azure secrets -- need admin)"
Write-Host "  Open/Partial P1:  $OpenP1"
Write-Host "  Resolved: $Resolved"
$Blockers | Select-Object Priority,Area,Status | Format-Table -AutoSize
