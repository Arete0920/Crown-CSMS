$ErrorActionPreference = "Continue"

$base = "audit-artifacts\release-verify"
New-Item -ItemType Directory -Force -Path $base | Out-Null

$BaseUrl = if ($env:CROWN_BASE_URL) { $env:CROWN_BASE_URL } else { "http://127.0.0.1:8000" }

$routes = @(
  "/api/v1/release-closeout/status/",
  "/api/v1/release-closeout/metrics/live/",
  "/api/v1/reports/transcript/DEMO-001/",
  "/api/v1/reports/report-card/DEMO-001/",
  "/api/v1/reports/discipline/DEMO-001/",
  "/api/v1/reports/board/",
  "/api/v1/notifications/sms/status/"
)

foreach ($route in $routes) {
  $name = ($route.Trim("/") -replace "[/\:]", "_") + ".txt"
  try {
    $resp = Invoke-WebRequest -Uri ($BaseUrl + $route) -Method Get -TimeoutSec 30
    @(
      "URL: $($BaseUrl + $route)"
      "Status: $($resp.StatusCode)"
      "Content-Type: $($resp.Headers['Content-Type'])"
    ) | Out-File "$base\$name" -Encoding utf8
  } catch {
    $_ | Out-String | Out-File "$base\$name" -Encoding utf8
  }
}

Write-Host "Portal/export verification written to $base"