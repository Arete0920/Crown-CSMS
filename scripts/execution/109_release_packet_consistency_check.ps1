param(
    [string]$RepoRoot
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if (-not $RepoRoot) {
    $RepoRoot = (git -C $PSScriptRoot\..\.. rev-parse --show-toplevel).Trim()
}

if ([string]::IsNullOrWhiteSpace($RepoRoot) -or -not (Test-Path $RepoRoot)) {
    throw 'Unable to resolve repository root.'
}

$releaseDir = Join-Path $RepoRoot 'audit-artifacts\release-readiness'
$topLevelFiles = @(
    Join-Path $releaseDir '00_MAY1_RELEASE_READINESS_STATUS.md'
    Join-Path $releaseDir '01_RELEASE_GATE_CHECKLIST.md'
    Join-Path $releaseDir '02_PRODUCTION_ACCEPTANCE_MATRIX.csv'
    Join-Path $releaseDir '07_FINAL_GO_NO_GO.md'
)

$allReleaseFiles = Get-ChildItem -Path $releaseDir -File

$goPatterns = @(
    '(?m)^May 1 Readiness Call:\s*GO\s*$'
    '(?m)^May 1 Readiness:\s*GO\s*$'
    '(?m)^GO for May 1\s*$'
    '(?m)^Decision:\s*APPROVED\s*$'
    '(?m)^Gate Result:\s*PASS\s*$'
)

$blockerPatterns = @(
    '(?m)^Result:\s*FAIL\s*$'
    '(?m)^Gate Result:\s*FAIL\s*$'
    '(?m)^.*NO-GO.*$'
    '\bpending\b'
    'pending signature'
    'signature pending'
    'needs approval'
    'Explicit decision:\s*NOT APPROVED'
    '\bNOT APPROVED\b'
    'not executed'
    'rollback pending'
    '\bTBD\b'
    'placeholder'
)

$issues = New-Object System.Collections.Generic.List[string]

function Get-FileText {
    param([string]$Path)
    return [System.IO.File]::ReadAllText($Path)
}

function Add-Issue {
    param([string]$Message)
    $issues.Add($Message)
}

function Find-LineMatches {
    param(
        [string]$Path,
        [string]$Pattern
    )

    $lineSearchResults = Select-String -Path $Path -Pattern $Pattern -CaseSensitive:$false
    foreach ($match in $lineSearchResults) {
        [pscustomobject]@{
            File = $Path
            Line = $match.LineNumber
            Text = $match.Line.Trim()
            Pattern = $Pattern
        }
    }
}

$topLevelTexts = @{}
foreach ($file in $topLevelFiles) {
    $topLevelTexts[$file] = Get-FileText -Path $file
}

$releaseReadinessMatches = @()
foreach ($file in $allReleaseFiles) {
    foreach ($pattern in $blockerPatterns) {
        $lineMatches = @(Find-LineMatches -Path $file.FullName -Pattern $pattern)
        if ($lineMatches.Count -gt 0) {
            $releaseReadinessMatches += $lineMatches
        }
    }
}

$topLevelImpliesGo = $false
foreach ($entry in $topLevelTexts.GetEnumerator()) {
    foreach ($pattern in $goPatterns) {
        if ($entry.Value -match $pattern) {
            $topLevelImpliesGo = $true
            break
        }
    }
}

if ($topLevelImpliesGo -and $releaseReadinessMatches.Count -gt 0) {
    Add-Issue 'Top-level GO/APPROVED language coexists with release-readiness blocker text.'
    foreach ($match in $releaseReadinessMatches) {
        $relativePath = Resolve-Path -LiteralPath $match.File -Relative
        Add-Issue ("  - {0}:{1}: {2}" -f $relativePath.TrimStart('.','\'), $match.Line, $match.Text)
    }
}

$statusText = $topLevelTexts[(Join-Path $releaseDir '00_MAY1_RELEASE_READINESS_STATUS.md')]
$checklistText = $topLevelTexts[(Join-Path $releaseDir '01_RELEASE_GATE_CHECKLIST.md')]
$finalText = $topLevelTexts[(Join-Path $releaseDir '07_FINAL_GO_NO_GO.md')]
$matrixText = $topLevelTexts[(Join-Path $releaseDir '02_PRODUCTION_ACCEPTANCE_MATRIX.csv')]

$summaryMatch = [regex]::Match($statusText, 'Summary:\s*(\d+) PASS\s*/\s*(\d+) FAIL')
$totalsMatch = [regex]::Match($finalText, 'Totals:\s*(\d+) PASS\s*/\s*(\d+) FAIL')
$checkPassMatch = [regex]::Match($checklistText, 'PASS:\s*(\d+)')
$checkFailMatch = [regex]::Match($checklistText, 'FAIL:\s*(\d+)')

$csvPass = ([regex]::Matches($matrixText, ',PASS,')).Count
$csvFail = ([regex]::Matches($matrixText, ',FAIL,')).Count

if ($summaryMatch.Success -and $totalsMatch.Success) {
    if ($summaryMatch.Groups[1].Value -ne $totalsMatch.Groups[1].Value -or $summaryMatch.Groups[2].Value -ne $totalsMatch.Groups[2].Value) {
        $issues.Add('00 and 07 gate totals disagree.')
    }
}

if ($summaryMatch.Success -and $checkPassMatch.Success -and $checkFailMatch.Success) {
    if ($summaryMatch.Groups[1].Value -ne $checkPassMatch.Groups[1].Value -or $summaryMatch.Groups[2].Value -ne $checkFailMatch.Groups[1].Value) {
        $issues.Add('00 and 01 gate totals disagree.')
    }
}

if ($summaryMatch.Success) {
    if ([int]$summaryMatch.Groups[1].Value -ne $csvPass -or [int]$summaryMatch.Groups[2].Value -ne $csvFail) {
        $issues.Add('Top-level totals do not match the production acceptance matrix counts.')
    }
}

if ($topLevelImpliesGo -and $csvFail -gt 0) {
    Add-Issue 'Top-level GO/APPROVED language is incompatible with nonzero FAIL gate counts in the production acceptance matrix.'
}

$gate4TopLevelFail = ($statusText -match 'Gate 4 Tenant Isolation Proof:\s*FAIL') -and ($checklistText -match '\| 4 \| Tenant Isolation Proof Gate \| FAIL \|') -and ($finalText -match 'Gate 4:\s*FAIL')
$gate4SubordinateBlocked = (Get-FileText -Path (Join-Path $releaseDir '04_SECURITY_TENANT_RELEASE_SIGNOFF.md')) -match 'Explicit decision:\s*NOT APPROVED'

if ($gate4TopLevelFail -and -not $gate4SubordinateBlocked) {
    Add-Issue 'Gate 4 is marked FAIL at the top level but the subordinate signoff file does not record NOT APPROVED.'
}

if (-not $gate4TopLevelFail -and $gate4SubordinateBlocked) {
    Add-Issue 'Gate 4 subordinate signoff is NOT APPROVED but top-level docs do not consistently show Gate 4 FAIL.'
}

if ($issues.Count -gt 0) {
    Write-Host 'Release packet consistency check: FAIL'
    foreach ($issue in $issues) {
        Write-Host $issue
    }
    exit 1
}

Write-Host 'Release packet consistency check: PASS'
Write-Host "Gate totals: PASS=$csvPass FAIL=$csvFail"
exit 0
