Set-Location C:\w\crown_main_postmerge_verify
$lr = (Get-Content "audit-artifacts/nonazure-production-readiness/LATEST.txt" -Raw).Trim()
$Out = "C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-phase2-validation\20260430_024221"

@(
  [pscustomobject]@{Finding='backend\tests\* (124 hits)'; Classification='SAFE'; Reason='All in test files, test-only passwords (pass1234, crownpass123).'; Action='None'}
  [pscustomobject]@{Finding='backend\crown_api\* TEST_AUTH_SECRET (63 hits)'; Classification='SAFE'; Reason='Test-only auth constant used in unit test overrides.'; Action='None'}
  [pscustomobject]@{Finding='backend\comms\email_service.py:32 _CLIENT_SECRET'; Classification='SAFE'; Reason='Reads from os.getenv(AZURE_CLIENT_SECRET, empty).'; Action='None'}
  [pscustomobject]@{Finding='backend\advancement\payments\providers.py:70'; Classification='SAFE'; Reason='Type annotation Optional[str]=None, no hardcoded value.'; Action='None'}
  [pscustomobject]@{Finding='backend\finance\api_views.py:67-309 client_secret'; Classification='SAFE'; Reason='Function definition and env-var-backed builder.'; Action='None'}
  [pscustomobject]@{Finding='backend\governance\microsoft_graph.py (4 hits)'; Classification='SAFE'; Reason='Env var name strings (M365_CLIENT_SECRET), not values.'; Action='None'}
  [pscustomobject]@{Finding='backend\integrations\graph_client.py (6 hits)'; Classification='SAFE'; Reason='Reads from GRAPH_CLIENT_SECRET / AZURE_CLIENT_SECRET env vars.'; Action='None'}
  [pscustomobject]@{Finding='backend\msauth\views.py:113 AZURE_CLIENT_SECRET'; Classification='SAFE'; Reason='Variable read from env var in OAuth2 token exchange.'; Action='None'}
  [pscustomobject]@{Finding='backend\create_superuser.py:17 password=Crown2026!'; Classification='FIXED'; Reason='Sandbox seed script. Was hardcoded + plaintext log. Fixed: env var + log redacted.'; Action='FIXED -- use DJANGO_SUPERUSER_PASSWORD env var to override default.'}
  [pscustomobject]@{Finding='backend\quarantine_old_tests\* (1 hit)'; Classification='SAFE'; Reason='Quarantined old test file, not in active test suite.'; Action='None'}
  [pscustomobject]@{Finding='scripts\execution\generate_215_fixes.py (3 hits)'; Classification='SAFE'; Reason='Dev tooling script generating fixture password strings. Not deployed.'; Action='None'}
  [pscustomobject]@{Finding='All other password= in test files (total ~295 pattern hits)'; Classification='SAFE'; Reason='169 password= patterns in test/seed files are expected test fixtures.'; Action='None'}
) | Export-Csv "$Out\22b_secret_scan_triage.csv" -NoTypeInformation

# Update blocker board: mark Security P0 as FIXED (one create_superuser fix, rest triaged SAFE)
$Ops = "C:\w\crown_main_postmerge_verify\docs\crown-master-binder\operations"
$LatestReadiness = $lr
$Blockers = @(
  [pscustomobject]@{Priority='P0'; Area='Security'; Issue='295 possible secret hits -- TRIAGED. 1 real fix applied (create_superuser.py). All others test fixtures or env-var reads. See 22b_secret_scan_triage.csv.'; Owner='Dev 5'; Evidence="$Out\22b_secret_scan_triage.csv"; RequiredFix='DONE. Set DJANGO_SUPERUSER_PASSWORD env var in deployment to override default.'; Status='RESOLVED'}
  [pscustomobject]@{Priority='P0'; Area='Deployment'; Issue='AZURE_SWA_TOKEN missing as repo secret.'; Owner='Azure admin'; Evidence='GitHub Settings > Secrets and variables > Actions'; RequiredFix='Add AZURE_SWA_TOKEN from Azure Portal > Static Web Apps > crown-dash > Manage deployment token.'; Status='Open'}
  [pscustomobject]@{Priority='P0'; Area='Deployment'; Issue='AZURE_CREDENTIALS missing from production environment.'; Owner='Azure admin'; Evidence='GitHub Settings > Environments > production > Secrets'; RequiredFix='Add AZURE_CREDENTIALS (Service Principal JSON) to production env secrets.'; Status='Open'}
  [pscustomobject]@{Priority='P0'; Area='Deployment'; Issue='Frontend HTTP 404 -- crown-dash not deployed.'; Owner='Azure admin'; Evidence='curl.exe https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/'; RequiredFix='Fix AZURE_SWA_TOKEN then rerun workflow 25139353897.'; Status='Open'}
  [pscustomobject]@{Priority='P1'; Area='UI/Product'; Issue='331 placeholder/incomplete markers in source.'; Owner='Dev 4 / Dev 5'; Evidence="$LatestReadiness\20_placeholder_scan.csv"; RequiredFix='Replace or defer each marker. Zero prod-facing placeholders before go-live.'; Status='Open'}
  [pscustomobject]@{Priority='P1'; Area='UI Polish'; Issue='52 UI anti-pattern hits (dark/broken/incomplete UI).'; Owner='Dev 4'; Evidence="$LatestReadiness\21_ui_antipattern_scan.csv"; RequiredFix='Replace dark/hardcoded treatments with CROWN light royal tokens.'; Status='Open'}
  [pscustomobject]@{Priority='P1'; Area='Accessibility'; Issue='514 accessibility review hits.'; Owner='Dev 4'; Evidence="$LatestReadiness\26_accessibility_review.csv"; RequiredFix='Fix critical (blocking) a11y items. Mark acceptable ones as deferred.'; Status='Open'}
  [pscustomobject]@{Priority='P2'; Area='Validation'; Issue='npm run lint + lint:fix produced minimal output -- verify clean in CI.'; Owner='Dev 5'; Evidence="$Out\validation_Frontend_Node_5.txt"; RequiredFix='Rerun lint in clean shell. Confirm zero ESLint errors.'; Status='Verify'}
  [pscustomobject]@{Priority='P2'; Area='Backend'; Issue='python manage.py check returned 0 issues -- verify same in staging.'; Owner='Dev 1'; Evidence="$Out\validation_Backend_Django_18.txt"; RequiredFix='Run django check in staging container. Confirm output matches.'; Status='Verify'}
)
$Blockers | Export-Csv "$Out\07_RELEASE_BLOCKER_BOARD.csv" -NoTypeInformation
Copy-Item "$Out\07_RELEASE_BLOCKER_BOARD.csv" "$Ops\12_RELEASE_BLOCKER_BOARD.csv" -Force
Write-Host "Blocker board updated."
Write-Host "Open P0: $(@($Blockers | Where-Object {$_.Priority -eq 'P0' -and $_.Status -eq 'Open'}).Count)"
Write-Host "Open P1: $(@($Blockers | Where-Object {$_.Priority -eq 'P1' -and $_.Status -eq 'Open'}).Count)"
