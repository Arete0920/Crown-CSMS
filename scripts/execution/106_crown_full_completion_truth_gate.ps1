param(
    [switch]$Deep
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($PSVersionTable.PSVersion.Major -ge 7) {
    $PSNativeCommandUseErrorActionPreference = $false
}

function Require-Tool {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required tool: $Name"
    }
}

function Resolve-PowerShellCommand {
    if (Get-Command pwsh -ErrorAction SilentlyContinue) { return "pwsh" }
    if (Get-Command powershell -ErrorAction SilentlyContinue) { return "powershell" }
    throw "Missing required tool: powershell/pwsh"
}

function New-Dir {
    param([string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Write-Utf8 {
    param([string]$Path, [string[]]$Lines)
    $Lines | Set-Content -Path $Path -Encoding UTF8
}

function Write-CsvSafe {
    param([string]$Path, [object[]]$Rows)
    if ($null -eq $Rows -or $Rows.Count -eq 0) {
        [pscustomobject]@{ Notice = "none" } | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    } else {
        $Rows | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    }
}

function Write-JsonFile {
    param([string]$Path, $Object)
    ($Object | ConvertTo-Json -Depth 12) | Set-Content -Path $Path -Encoding UTF8
}

function Test-KeywordsInFiles {
    param(
        [string[]]$Files,
        [string[]]$Keywords
    )

    if ($null -eq $Files -or $Files.Count -eq 0) { return $false }

    foreach ($f in $Files) {
        if (-not (Test-Path $f)) { continue }
        $content = ""
        try { $content = (Get-Content -Path $f -Raw -ErrorAction Stop).ToLowerInvariant() } catch { continue }
        foreach ($k in $Keywords) {
            if ($content -match [regex]::Escape($k.ToLowerInvariant())) {
                return $true
            }
        }
    }
    return $false
}

Require-Tool git
$shellExe = Resolve-PowerShellCommand

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}

Set-Location $repoRoot

$dirty = @((git status --porcelain=v1) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
if ($dirty.Count -gt 0) {
    throw "Worktree must be clean before full completion truth gate."
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\full-completion-truth\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\full-completion-truth\latest"
New-Dir $outDir
New-Dir $latestDir

$run105Log = Join-Path $outDir "10_run_105_dashboard_module_completion_gate_deep.txt"
$script105 = Join-Path $repoRoot "scripts\execution\105_dashboard_module_completion_gate.ps1"
$run105Passed = $false

if (Test-Path $script105) {
    $cmdArgs = @("-NoProfile", "-File", $script105, "-Deep")

    $global:LASTEXITCODE = 0
    & $shellExe @cmdArgs 1> $run105Log 2>&1
    $run105Code = $LASTEXITCODE
    if ($null -eq $run105Code) { $run105Code = 0 }
    $run105Passed = ($run105Code -eq 0)
} else {
    Write-Utf8 -Path $run105Log -Lines @("Missing script: $script105")
}

$manifestPath = Join-Path $repoRoot "frontend\dashboards\src\routes\wizard-manifest.js"
$routesPath = Join-Path $repoRoot "frontend\dashboards\src\routes\wizards.js"

if (-not (Test-Path $manifestPath)) { throw "Missing wizard manifest: $manifestPath" }
if (-not (Test-Path $routesPath)) { throw "Missing wizard route registry: $routesPath" }

$manifestRows = @()
$manifestText = Get-Content $manifestPath -Raw
$manifestBlocks = [regex]::Matches($manifestText, "(?s)\{[^{}]*\}")
foreach ($block in $manifestBlocks) {
    $slugMatch = [regex]::Match($block.Value, 'slug\s*:\s*["'']([^"'']+)["'']')
    $titleMatch = [regex]::Match($block.Value, 'title\s*:\s*["'']([^"'']+)["'']')
    $pathMatch = [regex]::Match($block.Value, 'path\s*:\s*["'']([^"'']+)["'']')
    if ($slugMatch.Success -and $titleMatch.Success -and $pathMatch.Success) {
        $manifestRows += [pscustomobject]@{
            Slug = $slugMatch.Groups[1].Value
            Title = $titleMatch.Groups[1].Value
            Path = $pathMatch.Groups[1].Value
        }
    }
}

$routeMap = @{}
$routeText = Get-Content $routesPath -Raw
$rawDefsMatch = [regex]::Match($routeText, "(?s)RAW_WIZARD_ROUTE_DEFINITIONS\s*=\s*\[(?<body>.*?)\]\s*;")
$routeBlockText = if ($rawDefsMatch.Success) { $rawDefsMatch.Groups["body"].Value } else { $routeText }
$routeMatches = [regex]::Matches($routeBlockText, "(?s)\{[^{}]*\}")
foreach ($m in $routeMatches) {
    $pathMatch = [regex]::Match($m.Value, 'path\s*:\s*["'']([^"'']+)["'']')
    $componentMatch = [regex]::Match($m.Value, 'component\s*:\s*([A-Za-z0-9_]+)')
    $nameMatch = [regex]::Match($m.Value, 'name\s*:\s*["'']([^"'']+)["'']')
    $rolesMatch = [regex]::Match($m.Value, '(?s)roles\s*:\s*\[(?<roles>[^\]]*)\]')
    if (-not ($pathMatch.Success -and $componentMatch.Success -and $nameMatch.Success)) { continue }

    $roles = @()
    foreach ($rm in [regex]::Matches($rolesMatch.Groups["roles"].Value, '["'']([^"'']+)["'']')) {
        $roles += $rm.Groups[1].Value
    }
    $routeMap[$pathMatch.Groups[1].Value] = [pscustomobject]@{
        Name = $nameMatch.Groups[1].Value
        Component = $componentMatch.Groups[1].Value
        Roles = $roles
    }
}

$searchRoots = @(
    Join-Path $repoRoot "frontend\dashboards\src",
    Join-Path $repoRoot "frontend\dashboards\tests",
    Join-Path $repoRoot "backend\tests",
    Join-Path $repoRoot "audit-artifacts"
) | Where-Object { Test-Path $_ }

$evidenceFiles = @()
foreach ($root in $searchRoots) {
    $evidenceFiles += @(Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
        $_.Extension.ToLowerInvariant() -in @(".js", ".jsx", ".ts", ".tsx", ".py", ".md", ".txt", ".json", ".png", ".jpg", ".jpeg", ".webp")
    })
}

$rows = @()
foreach ($wiz in $manifestRows) {
    $route = $null
    if ($routeMap.ContainsKey($wiz.Path)) {
        $route = $routeMap[$wiz.Path]
    }

    $componentPath = $null
    if ($null -ne $route) {
        foreach ($ext in @(".jsx", ".tsx", ".js", ".ts")) {
            $candidate = Join-Path $repoRoot ("frontend\dashboards\src\pages\" + $route.Component + $ext)
            if (Test-Path $candidate) {
                $componentPath = $candidate
                break
            }
        }
    }

    $slugToken = $wiz.Slug.ToLowerInvariant()
    $componentToken = if ($null -ne $route) { $route.Component.ToLowerInvariant() } else { "" }
    $related = @(
        $evidenceFiles | Where-Object {
            $p = $_.FullName.ToLowerInvariant()
            $p -like "*$slugToken*" -or (-not [string]::IsNullOrWhiteSpace($componentToken) -and $p -like "*$componentToken*")
        } | ForEach-Object { $_.FullName }
    )
    if (($null -eq $related -or $related.Count -eq 0) -and $null -ne $componentPath) {
        $related = @($componentPath)
    }

    $routeResolves = ($null -ne $route)
    $uiFlowRenders = ($routeResolves -and -not [string]::IsNullOrWhiteSpace($componentPath))
    $stepValidation = Test-KeywordsInFiles -Files $related -Keywords @("validate", "validation", "required", "invalid", "step")
    $saveResume = Test-KeywordsInFiles -Files $related -Keywords @("resume", "draft", "autosave", "save")
    $completionPersist = Test-KeywordsInFiles -Files $related -Keywords @("complete", "submit", "persist", "saved", "session")
    $permission = (($routeResolves -and $route.Roles.Count -gt 0) -or (Test-KeywordsInFiles -Files $related -Keywords @("permission", "rbac", "role", "forbidden", "403")))
    $failureState = Test-KeywordsInFiles -Files $related -Keywords @("error", "failure", "invalid", "exception", "400", "404")
    $testCoverage = [bool](@($related | Where-Object { $_ -match "(?i)test|spec|playwright|vitest|pytest|e2e" }).Count -gt 0)
    $artifactEvidence = (
        (Test-KeywordsInFiles -Files $related -Keywords @("screenshot", "tohavescreenshot", "playwright")) -or
        [bool](@($related | Where-Object { $_ -match "(?i)\.(png|jpg|jpeg|webp)$|playwright-report|test-results|audit-artifacts" }).Count -gt 0)
    )

    $allChecks = @(
        $routeResolves,
        $uiFlowRenders,
        $stepValidation,
        $saveResume,
        $completionPersist,
        $permission,
        $failureState,
        $testCoverage,
        $artifactEvidence
    )

    $runtimeState = if (@($allChecks | Where-Object { $_ -eq $false }).Count -eq 0) { "COMPLETE" } else { "INCOMPLETE" }

    $rows += [pscustomobject]@{
        Slug = $wiz.Slug
        Title = $wiz.Title
        Path = $wiz.Path
        RouteResolves = $routeResolves
        UiFlowRenders = $uiFlowRenders
        StepValidationEvidence = $stepValidation
        SaveResumeEvidence = $saveResume
        CompletionPersistenceEvidence = $completionPersist
        PermissionEnforcementEvidence = $permission
        FailureStateEvidence = $failureState
        TestCoverageEvidence = $testCoverage
        PlaywrightOrScreenshotEvidence = $artifactEvidence
        RuntimeState = $runtimeState
        EvidenceFileCount = @($related).Count
        EvidenceFiles = (@($related | Select-Object -First 20) -join "; ")
    }
}

$incompleteRows = @($rows | Where-Object { $_.RuntimeState -ne "COMPLETE" })
$unknownRows = @($rows | Where-Object { $_.RuntimeState -eq "UNKNOWN" })
$allComplete = ($incompleteRows.Count -eq 0)

Write-CsvSafe -Path (Join-Path $outDir "20_wizard_completion_matrix.csv") -Rows $rows

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("# Crown Full Completion Truth Gate Summary")
$summary.Add("")
$summary.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$summary.Add("- 105 dashboard gate deep pass: $run105Passed")
$summary.Add("- Evidence model: heuristic static scan (keywords + test/artifact traces)")
$summary.Add("- Wizard rows: $($rows.Count)")
$summary.Add("- COMPLETE rows: $(@($rows | Where-Object { $_.RuntimeState -eq 'COMPLETE' }).Count)")
$summary.Add("- INCOMPLETE rows: $($incompleteRows.Count)")
$summary.Add("- UNKNOWN rows: $($unknownRows.Count)")
$summary.Add("")
$summary.Add("## Verdict")
$summary.Add("")
if ($run105Passed -and $allComplete) {
    $summary.Add("PASS")
} else {
    $summary.Add("REVIEW REQUIRED")
}
$summary.Add("")

if ($incompleteRows.Count -gt 0) {
    $summary.Add("## Incomplete wizard rows")
    $summary.Add("")
    foreach ($r in $incompleteRows) {
        $summary.Add("- $($r.Title) [$($r.Slug)]")
    }
    $summary.Add("")
}

Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    repo_root = $repoRoot
    branch = (git branch --show-current).Trim()
    head = (git rev-parse HEAD).Trim()
    gate_105_deep = [ordered]@{
        passed = $run105Passed
        log = $run105Log
    }
    wizard_rows = $rows
    complete_count = @($rows | Where-Object { $_.RuntimeState -eq "COMPLETE" }).Count
    incomplete_count = $incompleteRows.Count
    unknown_count = $unknownRows.Count
    pass = ($run105Passed -and $allComplete)
}

Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host ""
Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "LATEST:  $(Join-Path $latestDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $outDir '99_STATUS.json')"
Write-Host ""

if (-not $status.pass) { exit 1 }
