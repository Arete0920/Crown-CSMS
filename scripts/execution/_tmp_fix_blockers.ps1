$Out  = 'C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-phase2-validation\20260430_024221'
$Ops  = 'C:\w\crown_main_postmerge_verify\docs\crown-master-binder\operations'
$LatestReadiness = (Get-Content 'C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-production-readiness\LATEST.txt' -Raw).Trim()

$Blockers = @(
  [pscustomobject]@{Priority='P0'; Area='Security'; Issue='295 possible secret/token hits require classification.'; Owner='Dev 5'; Evidence="$LatestReadiness\22_possible_secret_scan.csv"; RequiredFix='Triage each hit: real secret vs test fixture vs false positive. Rotate any real secrets immediately.'; Status='Open'}
  [pscustomobject]@{Priority='P0'; Area='Deployment'; Issue='AZURE_SWA_TOKEN missing as repo secret.'; Owner='Azure admin'; Evidence='GitHub Settings > Secrets and variables > Actions'; RequiredFix='Add AZURE_SWA_TOKEN from Azure Portal > Static Web Apps > crown-dash > Manage deployment token.'; Status='Open'}
  [pscustomobject]@{Priority='P0'; Area='Deployment'; Issue='AZURE_CREDENTIALS missing from production environment.'; Owner='Azure admin'; Evidence='GitHub Settings > Environments > production > Secrets'; RequiredFix='Add AZURE_CREDENTIALS (Service Principal JSON) to production env secrets.'; Status='Open'}
  [pscustomobject]@{Priority='P0'; Area='Deployment'; Issue='Frontend HTTP 404 -- crown-dash not deployed.'; Owner='Azure admin'; Evidence='curl.exe https://crown-dash.azurestaticapps.net/'; RequiredFix='Fix AZURE_SWA_TOKEN then rerun workflow 25139353897.'; Status='Open'}
  [pscustomobject]@{Priority='P1'; Area='UI/Product'; Issue='331 placeholder/incomplete markers in source.'; Owner='Dev 4 / Dev 5'; Evidence="$LatestReadiness\20_placeholder_scan.csv"; RequiredFix='Replace or defer each marker. Zero prod-facing placeholders before go-live.'; Status='Open'}
  [pscustomobject]@{Priority='P1'; Area='UI Polish'; Issue='52 UI anti-pattern hits (dark/broken/incomplete UI).'; Owner='Dev 4'; Evidence="$LatestReadiness\21_ui_antipattern_scan.csv"; RequiredFix='Replace dark/hardcoded treatments with CROWN light royal tokens.'; Status='Open'}
  [pscustomobject]@{Priority='P1'; Area='Accessibility'; Issue='514 accessibility review hits.'; Owner='Dev 4'; Evidence="$LatestReadiness\26_accessibility_review.csv"; RequiredFix='Fix critical (blocking) a11y items. Mark acceptable ones as deferred.'; Status='Open'}
  [pscustomobject]@{Priority='P2'; Area='Validation'; Issue='npm run lint + lint:fix produced minimal output -- verify clean in CI.'; Owner='Dev 5'; Evidence="$Out\validation_Frontend_Node_5.txt"; RequiredFix='Rerun lint in clean shell. Confirm zero ESLint errors.'; Status='Verify'}
  [pscustomobject]@{Priority='P2'; Area='Backend'; Issue='python manage.py check returned 0 issues -- verify same in staging.'; Owner='Dev 1'; Evidence="$Out\validation_Backend_Django_18.txt"; RequiredFix='Run django check in staging container. Confirm output matches.'; Status='Verify'}
)
$Blockers | Export-Csv "$Out\07_RELEASE_BLOCKER_BOARD.csv" -NoTypeInformation
Copy-Item "$Out\07_RELEASE_BLOCKER_BOARD.csv" "$Ops\12_RELEASE_BLOCKER_BOARD.csv" -Force
Write-Host "Blocker board written:"
$Blockers | Select-Object Priority,Area,Owner,Status,Issue | Format-Table -AutoSize
