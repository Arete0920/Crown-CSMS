param(
  [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$scan = "docs\audit\scans"
New-Item -ItemType Directory -Force -Path $scan | Out-Null

function Export-Utf8Csv {
  param(
    [Parameter(Mandatory=$true)]$Rows,
    [Parameter(Mandatory=$true)][string]$Path
  )
  $Rows | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
}

function Collect-Hits {
  param(
    [string[]]$Files,
    [string[]]$Patterns,
    [string]$OutPath
  )

  $rows = @()
  foreach ($pat in $Patterns) {
    $hits = Select-String -Path $Files -Pattern $pat -SimpleMatch -ErrorAction SilentlyContinue
    foreach ($h in $hits) {
      $rows += [pscustomobject]@{
        Path = $h.Path
        LineNumber = $h.LineNumber
        Pattern = $pat
        Line = $h.Line.Trim()
      }
    }
  }

  Export-Utf8Csv -Rows $rows -Path $OutPath
}

$allTextFiles = Get-ChildItem . -Recurse -File -Include *.py,*.js,*.jsx,*.ts,*.tsx,*.yml,*.yaml,*.md,*.json -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName

Collect-Hits -Files $allTextFiles -Patterns @("TODO","FIXME","HACK","XXX") -OutPath "$scan\TODO_SCAN.csv"

Collect-Hits -Files $allTextFiles -Patterns @(
  "00000000-0000-0000-0000-000000000000",
  "11111111-1111-1111-1111-111111111111",
  "placeholder",
  "mock",
  "dummy",
  "example123",
  "TestAuthSecret-LocalOnly"
) -OutPath "$scan\PLACEHOLDER_SCAN.csv"

Collect-Hits -Files $allTextFiles -Patterns @(
  "api/v1/v1",
  "urlpatterns",
  "router.register",
  "path(",
  "include(",
  "re_path("
) -OutPath "$scan\ROUTE_RISK_SCAN.csv"

Collect-Hits -Files $allTextFiles -Patterns @(
  "if: always(",
  "workflow_dispatch:",
  "pull_request:",
  "push:",
  "schedule:",
  "actions/checkout@v5",
  "actions/setup-python@v5"
) -OutPath "$scan\WORKFLOW_RISK_SCAN.csv"

Collect-Hits -Files $allTextFiles -Patterns @(
  "demo-ready",
  "pilot-ready",
  "credible operating MVP",
  "deferred",
  "bounded remaining work",
  "production-hardening in progress"
) -OutPath "$scan\DOC_CLAIM_SCAN.csv"

$dupes = Get-ChildItem . -Recurse -File -ErrorAction SilentlyContinue |
  Group-Object Name |
  Where-Object { $_.Count -gt 1 } |
  ForEach-Object {
    foreach ($i in $_.Group) {
      [pscustomobject]@{
        Name = $_.Name
        Count = $_.Count
        Path = $i.FullName
      }
    }
  }
Export-Utf8Csv -Rows $dupes -Path "$scan\DUPLICATE_FILENAME_SCAN.csv"

$uiFiles = Get-ChildItem "frontend" -Recurse -File -Include *.jsx,*.tsx,*.js,*.ts -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
if ($uiFiles.Count -gt 0) {
  Collect-Hits -Files $uiFiles -Patterns @(
    "TODO",
    "FIXME",
    "mock",
    "dummy",
    "placeholder",
    "00000000-0000-0000-0000-000000000000",
    "11111111-1111-1111-1111-111111111111"
  ) -OutPath "$scan\DASHBOARD_WIZARD_RISK_SCAN.csv"
} else {
  @() | Export-Csv "$scan\DASHBOARD_WIZARD_RISK_SCAN.csv" -NoTypeInformation -Encoding UTF8
}

Write-Host "Static scans complete."
Write-Host "Open docs\audit\scans\*.csv"
