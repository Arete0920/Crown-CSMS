powershell -NoProfile -ExecutionPolicy Bypass -Command "
Set-Location C:\w\crown_main_postmerge_verify
$lr = (Get-Content 'audit-artifacts/nonazure-production-readiness/LATEST.txt' -Raw).Trim()
$Out = 'audit-artifacts/nonazure-phase2-validation/20260430_024221'

# Write triage CSV
@(
  [pscustomobject]@{Finding='backend\tests\* (124 hits)'; Classification='SAFE'; Reason='All in test files, test-only passwords (pass1234 / pass12345 / crownpass123).'; Action='None'}
  [pscustomobject]@{Finding='backend\crown_api\* TEST_AUTH_SECRET (63 hits)'; Classification='SAFE'; Reason='Test-only auth constant used in unit test overrides.'; Action='None'}
  [pscustomobject]@{Finding='backend\comms\email_service.py:32 _CLIENT_SECRET'; Classification='SAFE'; Reason='Reads from os.getenv(AZURE_CLIENT_SECRET, empty).'; Action='None'}
  [pscustomobject]@{Finding='backend\advancement\payments\providers.py:70 client_secret'; Classification='SAFE'; Reason='Type annotation Optional[str]=None, no hardcoded value.'; Action='None'}
  [pscustomobject]@{Finding='backend\finance\api_views.py:67-309 client_secret'; Classification='SAFE'; Reason='Function definition and env-var-backed builder, no hardcoded value.'; Action='None'}
  [pscustomobject]@{Finding='backend\governance\microsoft_graph.py (4 hits)'; Classification='SAFE'; Reason='Env var name strings (M365_CLIENT_SECRET), not values.'; Action='None'}
  [pscustomobject]@{Finding='backend\integrations\graph_client.py (6 hits)'; Classification='SAFE'; Reason='Reads from GRAPH_CLIENT_SECRET / AZURE_CLIENT_SECRET env vars.'; Action='None'}
  [pscustomobject]@{Finding='backend\msauth\views.py:113 AZURE_CLIENT_SECRET'; Classification='SAFE'; Reason='Variable read from env var in OAuth2 token exchange.'; Action='None'}
  [pscustomobject]@{Finding='backend\create_superuser.py:17 password=Crown2026!'; Classification='FIXED'; Reason='Sandbox seed script only. Was hardcoded with plaintext log. Fixed: env var + log redacted.'; Action='FIXED in this PR -- use DJANGO_SUPERUSER_PASSWORD env var to override.'}
  [pscustomobject]@{Finding='backend\quarantine_old_tests\* (1 hit)'; Classification='SAFE'; Reason='Quarantined old test file, not in active test suite.'; Action='None'}
  [pscustomobject]@{Finding='scripts\execution\generate_215_fixes.py (3 hits)'; Classification='SAFE'; Reason='Dev tooling script generating fixture password strings. Not deployed.'; Action='None'}
  [pscustomobject]@{Finding='All other password= in test files'; Classification='SAFE'; Reason='169 password= patterns in test/seed files are expected test fixtures.'; Action='None'}
) | Export-Csv '$Out/22b_secret_scan_triage.csv' -NoTypeInformation
Write-Host 'Triage written.'
"
