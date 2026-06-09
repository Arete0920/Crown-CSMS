param(
    [string]$OutputRoot = "audit-artifacts/wizard-parity",
    [switch]$FailOnIncomplete
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function New-Dir {
    param([string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Write-Utf8 {
    param([string]$Path, [string[]]$Lines)
    $Lines | Set-Content -Path $Path -Encoding UTF8
}

function Write-JsonFile {
    param([string]$Path, $Object)
    ($Object | ConvertTo-Json -Depth 12) | Set-Content -Path $Path -Encoding UTF8
}

function Write-CsvSafe {
    param([string]$Path, [object[]]$Rows)
    if ($null -eq $Rows -or $Rows.Count -eq 0) {
        [pscustomobject]@{ Notice = "none" } | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    } else {
        $Rows | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    }
}

function Get-ObjectBlocks {
    param([string]$Text)

    $blocks = New-Object System.Collections.Generic.List[string]
    $depth = 0
    $start = -1
    $inString = $false
    $quote = [char]0
    $escape = $false

    for ($i = 0; $i -lt $Text.Length; $i++) {
        $ch = $Text[$i]

        if ($inString) {
            if ($escape) {
                $escape = $false
                continue
            }
            if ($ch -eq '\') {
                $escape = $true
                continue
            }
            if ($ch -eq $quote) {
                $inString = $false
            }
            continue
        }

        if ($ch -eq '"' -or $ch -eq "'") {
            $inString = $true
            $quote = $ch
            continue
        }

        if ($ch -eq '{') {
            if ($depth -eq 0) { $start = $i }
            $depth++
            continue
        }

        if ($ch -eq '}') {
            if ($depth -gt 0) { $depth-- }
            if ($depth -eq 0 -and $start -ge 0) {
                $blocks.Add($Text.Substring($start, ($i - $start + 1))) | Out-Null
                $start = -1
            }
        }
    }

    return @($blocks.ToArray())
}

function Get-StringProperty {
    param(
        [string]$Block,
        [string]$Name
    )

    $pattern = ('(?m){0}\s*:\s*["'']([^"'']+)["'']' -f [regex]::Escape($Name))
    $m = [regex]::Match($Block, $pattern)
    if ($m.Success) { return $m.Groups[1].Value }
    return ""
}

function Get-ArrayStringsProperty {
    param(
        [string]$Block,
        [string]$Name
    )

    $pattern = ('(?s){0}\s*:\s*\[(?<body>.*?)\]' -f [regex]::Escape($Name))
    $m = [regex]::Match($Block, $pattern)
    if (-not $m.Success) { return @() }

    $values = New-Object System.Collections.Generic.List[string]
    foreach ($item in [regex]::Matches($m.Groups['body'].Value, '["'']([^"'']+)["'']')) {
        $values.Add($item.Groups[1].Value) | Out-Null
    }
    return @($values.ToArray())
}

function Normalize-ApiPrefix {
    param([string]$Value)

    $v = ("$Value").Trim()
    if ([string]::IsNullOrWhiteSpace($v)) { return "" }
    $v = $v -replace '^/', ''
    if ($v -notmatch '/$') { $v = "$v/" }
    return $v
}

function Normalize-Path {
    param([string]$Value)

    $v = ("$Value").Trim()
    if ([string]::IsNullOrWhiteSpace($v)) { return "" }
    if ($v -notmatch '^/') { $v = "/$v" }
    return $v
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}
Set-Location $repoRoot

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot (Join-Path $OutputRoot $stamp)
$latestDir = Join-Path $repoRoot (Join-Path $OutputRoot "latest")
New-Dir $outDir
New-Dir $latestDir

$frontendPath = Join-Path $repoRoot "frontend/dashboards/src/routes/wizards.js"
$backendPath = Join-Path $repoRoot "backend/crown_api/wizard_registry.py"

if (-not (Test-Path $frontendPath)) { throw "Missing frontend wizard registry: $frontendPath" }
if (-not (Test-Path $backendPath)) { throw "Missing backend wizard registry: $backendPath" }

$frontendText = Get-Content $frontendPath -Raw
$backendText = Get-Content $backendPath -Raw

$frontendRows = New-Object System.Collections.Generic.List[object]
$backendRows = New-Object System.Collections.Generic.List[object]

$frontendArray = [regex]::Match($frontendText, '(?s)RAW_WIZARD_ROUTE_DEFINITIONS\s*=\s*\[(?<body>.*?)\]\s*;')
$frontendBlockText = if ($frontendArray.Success) { $frontendArray.Groups['body'].Value } else { $frontendText }
foreach ($block in Get-ObjectBlocks $frontendBlockText) {
    $path = Normalize-Path (Get-StringProperty -Block $block -Name "path")
    $name = Get-StringProperty -Block $block -Name "name"
    $apiPrefix = Normalize-ApiPrefix (Get-StringProperty -Block $block -Name "apiPrefix")
    $releaseState = Get-StringProperty -Block $block -Name "releaseState"
    $roles = Get-ArrayStringsProperty -Block $block -Name "roles"
    $component = ""
    $cm = [regex]::Match($block, '(?m)component\s*:\s*([A-Za-z0-9_]+)')
    if ($cm.Success) { $component = $cm.Groups[1].Value }

    if (-not [string]::IsNullOrWhiteSpace($path)) {
        $frontendRows.Add([pscustomobject]@{
            Name = $name
            Path = $path
            ApiPrefix = $apiPrefix
            Component = $component
            ReleaseState = if ([string]::IsNullOrWhiteSpace($releaseState)) { "draft" } else { $releaseState }
            Roles = ($roles -join ';')
        }) | Out-Null
    }
}

foreach ($block in Get-ObjectBlocks $backendText) {
    $name = Get-StringProperty -Block $block -Name "name"
    $appConfig = Get-StringProperty -Block $block -Name "app_config"
    $urlPrefix = Normalize-ApiPrefix (Get-StringProperty -Block $block -Name "url_prefix")
    $urlsModule = Get-StringProperty -Block $block -Name "urls_module"

    if (-not [string]::IsNullOrWhiteSpace($urlPrefix)) {
        $backendRows.Add([pscustomobject]@{
            Name = $name
            AppConfig = $appConfig
            UrlPrefix = $urlPrefix
            UrlsModule = $urlsModule
        }) | Out-Null
    }
}

$backendByPrefix = @{}
foreach ($b in $backendRows) {
    if (-not $backendByPrefix.ContainsKey($b.UrlPrefix)) {
        $backendByPrefix[$b.UrlPrefix] = $b
    }
}

$frontendByPrefix = @{}
foreach ($f in $frontendRows) {
    if (-not [string]::IsNullOrWhiteSpace($f.ApiPrefix) -and -not $frontendByPrefix.ContainsKey($f.ApiPrefix)) {
        $frontendByPrefix[$f.ApiPrefix] = $f
    }
}

$matrix = New-Object System.Collections.Generic.List[object]
foreach ($f in $frontendRows) {
    $backend = $null
    $backendFound = (-not [string]::IsNullOrWhiteSpace($f.ApiPrefix)) -and $backendByPrefix.ContainsKey($f.ApiPrefix)
    if ($backendFound) { $backend = $backendByPrefix[$f.ApiPrefix] }

    $componentPath = ""
    if (-not [string]::IsNullOrWhiteSpace($f.Component)) {
        foreach ($ext in @('.jsx', '.tsx', '.js', '.ts')) {
            $candidate = Join-Path $repoRoot ("frontend/dashboards/src/pages/{0}{1}" -f $f.Component, $ext)
            if (Test-Path $candidate) {
                $componentPath = $candidate.Replace($repoRoot + [System.IO.Path]::DirectorySeparatorChar, '')
                break
            }
        }
    }

    $matrix.Add([pscustomobject]@{
        FrontendName = $f.Name
        FrontendPath = $f.Path
        FrontendApiPrefix = $f.ApiPrefix
        FrontendComponent = $f.Component
        FrontendReleaseState = $f.ReleaseState
        FrontendRoles = $f.Roles
        BackendFound = $backendFound
        BackendName = if ($backendFound) { $backend.Name } else { "" }
        BackendUrlPrefix = if ($backendFound) { $backend.UrlPrefix } else { "" }
        BackendAppConfig = if ($backendFound) { $backend.AppConfig } else { "" }
        BackendUrlsModule = if ($backendFound) { $backend.UrlsModule } else { "" }
        ComponentFound = -not [string]::IsNullOrWhiteSpace($componentPath)
        ComponentPath = $componentPath
        RolesDeclared = -not [string]::IsNullOrWhiteSpace($f.Roles)
        Decision = if ($backendFound -and -not [string]::IsNullOrWhiteSpace($componentPath) -and -not [string]::IsNullOrWhiteSpace($f.Roles)) { "PASS" } else { "REVIEW_REQUIRED" }
    }) | Out-Null
}

foreach ($b in $backendRows) {
    if (-not $frontendByPrefix.ContainsKey($b.UrlPrefix)) {
        $matrix.Add([pscustomobject]@{
            FrontendName = ""
            FrontendPath = ""
            FrontendApiPrefix = ""
            FrontendComponent = ""
            FrontendReleaseState = ""
            FrontendRoles = ""
            BackendFound = $true
            BackendName = $b.Name
            BackendUrlPrefix = $b.UrlPrefix
            BackendAppConfig = $b.AppConfig
            BackendUrlsModule = $b.UrlsModule
            ComponentFound = $false
            ComponentPath = ""
            RolesDeclared = $false
            Decision = "BACKEND_ONLY_REVIEW_REQUIRED"
        }) | Out-Null
    }
}

$rows = @($matrix.ToArray())
$reviewRows = @($rows | Where-Object { $_.Decision -ne "PASS" })

Write-CsvSafe -Path (Join-Path $outDir "20_wizard_frontend_backend_parity.csv") -Rows $rows
Write-CsvSafe -Path (Join-Path $outDir "21_wizard_frontend_rows.csv") -Rows @($frontendRows.ToArray())
Write-CsvSafe -Path (Join-Path $outDir "22_wizard_backend_rows.csv") -Rows @($backendRows.ToArray())
Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object ([ordered]@{
    generated_at = (Get-Date).ToString("s")
    repo_root = $repoRoot
    branch = (git branch --show-current).Trim()
    head = (git rev-parse HEAD).Trim()
    frontend_count = @($frontendRows.ToArray()).Count
    backend_count = @($backendRows.ToArray()).Count
    matrix_count = $rows.Count
    review_required_count = $reviewRows.Count
    pass = ($reviewRows.Count -eq 0)
})

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("# Wizard Frontend/Backend Parity Summary")
$summary.Add("")
$summary.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$summary.Add("- Frontend wizard routes: $(@($frontendRows.ToArray()).Count)")
$summary.Add("- Backend wizard entries: $(@($backendRows.ToArray()).Count)")
$summary.Add("- Matrix rows: $($rows.Count)")
$summary.Add("- Review required rows: $($reviewRows.Count)")
$summary.Add("")
$summary.Add("## Verdict")
$summary.Add("")
if ($reviewRows.Count -eq 0) {
    $summary.Add("PASS")
} else {
    $summary.Add("REVIEW REQUIRED")
    $summary.Add("")
    $summary.Add("## Rows requiring review")
    foreach ($r in $reviewRows) {
        $label = if (-not [string]::IsNullOrWhiteSpace($r.FrontendPath)) { $r.FrontendPath } else { $r.BackendUrlPrefix }
        $summary.Add("- $label :: $($r.Decision)")
    }
}
Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "WIZARD_PARITY_EVIDENCE=$outDir"
Write-Host "WIZARD_PARITY_SUMMARY=$(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "WIZARD_PARITY_MATRIX=$(Join-Path $outDir '20_wizard_frontend_backend_parity.csv')"

if ($FailOnIncomplete -and $reviewRows.Count -gt 0) {
    exit 1
}
