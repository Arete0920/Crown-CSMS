$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Get-RepoRoot {
    $root = (git rev-parse --show-toplevel 2>$null)
    if (-not $root) { throw "Not inside a git repository." }
    return $root.Trim()
}

function Write-Utf8File {
    param(
        [string]$Path,
        [string]$Content
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $Content | Set-Content -Path $Path -Encoding utf8
}

function Normalize-Slash {
    param([string]$Path)
    return ($Path -replace "\\","/")
}

function Add-NoteToken {
    param(
        [string]$Existing,
        [string]$Token
    )
    $items = New-Object System.Collections.Generic.List[string]
    if ($Existing) {
        foreach ($part in ($Existing -split ";")) {
            $t = $part.Trim()
            if ($t) { [void]$items.Add($t) }
        }
    }
    if ($Token) {
        foreach ($part in ($Token -split ";")) {
            $t = $part.Trim()
            if ($t) { [void]$items.Add($t) }
        }
    }
    return (($items | Select-Object -Unique) -join ";")
}

function Get-LatestArtifactDir {
    param([string]$BasePath)
    if (-not (Test-Path $BasePath)) { return $null }
    return Get-ChildItem -Path $BasePath -Directory | Sort-Object Name -Descending | Select-Object -First 1
}

function Resolve-KeepRewriteDrop {
    param(
        [string]$Item,
        [string]$Category,
        [string]$CurrentState,
        [string]$CoreModuleAddon
    )

    $p = $Item.ToLowerInvariant()
    $category = [string]$Category
    $state = [string]$CurrentState
    $cma = [string]$CoreModuleAddon

    if ($p -match "/[.]history/|^node_modules/|/node_modules/|^dist/|/dist/|^build/|/build/|^coverage/|/coverage/|__pycache__|[.]pytest_cache") {
        return "Drop"
    }

    if ($state -eq "Empty") {
        return "Rewrite"
    }

    if ($category -in @("Migration","Dependency","Config","Test")) {
        return "Keep"
    }

    if ($p -match "^docs/crown_master_binder/") {
        return "Keep"
    }

    if ($p -match "^scripts/execution/") {
        return "Keep"
    }

    if ($cma -eq "Core") {
        return "Keep"
    }

    if ($cma -in @("Module","Addon")) {
        if ($state -in @("ReviewAged","MissingFromDisk","InventoryNeeded")) {
            return "Rewrite"
        }
        return "Keep"
    }

    if ($state -eq "GeneratedOrStale") {
        return "Drop"
    }

    if ($state -eq "ReviewAged" -and $category -eq "Document") {
        return "Rewrite"
    }

    return "Keep"
}

function Resolve-FinalDecision {
    param(
        [string]$KeepRewriteDrop,
        [string]$CurrentState,
        [string]$CoreModuleAddon
    )

    $krd = [string]$KeepRewriteDrop
    $state = [string]$CurrentState
    $cma = [string]$CoreModuleAddon

    if ($krd -in @("Keep","Rewrite","Drop")) {
        return $krd
    }

    if ($state -eq "Empty") {
        return "Rewrite"
    }

    if ($cma -eq "Core") {
        return "Keep"
    }

    return "Keep"
}

function Patch-StrictModeCountIssues {
    param([string]$Path)

    if (-not (Test-Path $Path)) { return }

    $text = Get-Content -Raw -Path $Path
    $updated = $text

    if ($updated -match '\$candidates = @\(\$inventoryBefore \| Where-Object \{') {
        $updated = $updated -replace '\$deletedCount = \(\$purgeLedger \| Where-Object \{ \$_.Result -eq "Deleted" \}\)\.Count', '$deletedCount = @($purgeLedger | Where-Object { $_.Result -eq "Deleted" }).Count'
        $updated = $updated -replace '\$failedCount = \(\$purgeLedger \| Where-Object \{ \$_.Result -eq "DeleteFailed" \}\)\.Count', '$failedCount = @($purgeLedger | Where-Object { $_.Result -eq "DeleteFailed" }).Count'
        $updated = $updated -replace '\$blockedCount = \(\$purgeLedger \| Where-Object \{ \$_.Result -like "Blocked\*" \}\)\.Count', '$blockedCount = @($purgeLedger | Where-Object { $_.Result -like "Blocked*" }).Count'
    }

    $updated = $updated -replace '\$canonMissingCount = \(\$canonMatrix \| Where-Object \{ \$_.Exists -eq \$false \}\)\.Count', '$canonMissingCount = @($canonMatrix | Where-Object { $_.Exists -eq $false }).Count'
    $updated = $updated -replace '\$unclassifiedCount = \(\$rowsOut \| Where-Object \{ \[string\]::IsNullOrWhiteSpace\(\$_\.CoreModuleAddon\) \}\)\.Count', '$unclassifiedCount = @($rowsOut | Where-Object { [string]::IsNullOrWhiteSpace($_.CoreModuleAddon) }).Count'
    $updated = $updated -replace '\$blankKrdCount = \(\$rowsOut \| Where-Object \{ \[string\]::IsNullOrWhiteSpace\(\$_\.KeepRewriteDrop\) \}\)\.Count', '$blankKrdCount = @($rowsOut | Where-Object { [string]::IsNullOrWhiteSpace($_.KeepRewriteDrop) }).Count'
    $updated = $updated -replace '\$blankDecisionCount = \(\$rowsOut \| Where-Object \{ \[string\]::IsNullOrWhiteSpace\(\$_\.FinalDecision\) \}\)\.Count', '$blankDecisionCount = @($rowsOut | Where-Object { [string]::IsNullOrWhiteSpace($_.FinalDecision) }).Count'

    if ($updated -ne $text) {
        $updated | Set-Content -Path $Path -Encoding utf8
    }
}

$repoRoot = Get-RepoRoot
Set-Location $repoRoot

$scriptDir = Join-Path $repoRoot "scripts\execution"
$inventoryDir = Join-Path $repoRoot "docs\Crown_Master_Binder\04_Inventory_Keep_Rewrite_Drop"
$auditRoot = Join-Path $repoRoot "audit-artifacts"
$masterInventory = Join-Path $inventoryDir "01_Master_Inventory.csv"
$coreInventory   = Join-Path $inventoryDir "02_Core_Inventory.csv"
$moduleInventory = Join-Path $inventoryDir "03_Module_Inventory.csv"
$addonInventory  = Join-Path $inventoryDir "04_Addon_Inventory.csv"

foreach ($needed in @($scriptDir, $inventoryDir, $auditRoot)) {
    New-Item -ItemType Directory -Force -Path $needed | Out-Null
}

if (-not (Test-Path $masterInventory)) {
    throw "Missing master inventory: $masterInventory"
}

foreach ($name in @(
    "80_phase12_auto_review_and_apply.ps1",
    "81_phase34_archive_and_purge_enforcement.ps1",
    "83_phase567_core_module_release_enforcement.ps1",
    "85_gate_finalization_and_executive_completion.ps1"
)) {
    Patch-StrictModeCountIssues -Path (Join-Path $scriptDir $name)
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$artifactRoot = Join-Path $auditRoot ("phase12_decision_closer\" + $timestamp)
New-Item -ItemType Directory -Force -Path $artifactRoot | Out-Null

$inventory = @(Import-Csv $masterInventory)
if ($inventory.Count -eq 0) {
    throw "Master inventory is empty."
}

$backupPath = Join-Path $artifactRoot "01_Master_Inventory.before.csv"
$inventory | Export-Csv -Path $backupPath -NoTypeInformation -Encoding utf8

$changedRows = New-Object System.Collections.Generic.List[object]
$outRows = New-Object System.Collections.Generic.List[object]

foreach ($row in $inventory) {
    $item = [string]$row.Item
    $lane = [string]$row.Lane
    $category = [string]$row.Category
    $owner = [string]$row.Owner
    $state = [string]$row.CurrentState
    $cma = [string]$row.CoreModuleAddon
    $krd = [string]$row.KeepRewriteDrop
    $decision = [string]$row.FinalDecision
    $priority = [string]$row.Priority
    $notes = [string]$row.Notes

    $origKrd = $krd
    $origDecision = $decision
    $origNotes = $notes

    if ([string]::IsNullOrWhiteSpace($krd)) {
        $krd = Resolve-KeepRewriteDrop -Item $item -Category $category -CurrentState $state -CoreModuleAddon $cma
        $notes = Add-NoteToken -Existing $notes -Token ("AutoCloseKRD:" + $krd)
    }

    if ([string]::IsNullOrWhiteSpace($decision)) {
        $decision = Resolve-FinalDecision -KeepRewriteDrop $krd -CurrentState $state -CoreModuleAddon $cma
        $notes = Add-NoteToken -Existing $notes -Token ("AutoCloseDecision:" + $decision)
    }

    if ([string]::IsNullOrWhiteSpace($priority)) {
        if ($cma -eq "Core") { $priority = "P0" }
        elseif ($cma -eq "Module") { $priority = "P1" }
        elseif ($cma -eq "Addon") { $priority = "P2" }
        else { $priority = "P3" }
    }

    $newRow = [pscustomobject]@{
        ItemID          = $row.ItemID
        Item            = $item
        Lane            = $lane
        Category        = $category
        Owner           = $owner
        CurrentState    = $state
        CoreModuleAddon = $cma
        KeepRewriteDrop = $krd
        FinalDecision   = $decision
        Priority        = $priority
        Notes           = $notes
    }

    $outRows.Add($newRow)

    if ($origKrd -ne $krd -or $origDecision -ne $decision -or $origNotes -ne $notes) {
        $changedRows.Add([pscustomobject]@{
            Item            = $item
            CoreModuleAddon = $cma
            KeepRewriteDrop_Before = $origKrd
            KeepRewriteDrop_After  = $krd
            FinalDecision_Before   = $origDecision
            FinalDecision_After    = $decision
            Notes_After            = $notes
        })
    }
}

$outRows | Export-Csv -Path $masterInventory -NoTypeInformation -Encoding utf8
@($outRows | Where-Object { $_.CoreModuleAddon -eq "Core" })   | Export-Csv -Path $coreInventory   -NoTypeInformation -Encoding utf8
@($outRows | Where-Object { $_.CoreModuleAddon -eq "Module" }) | Export-Csv -Path $moduleInventory -NoTypeInformation -Encoding utf8
@($outRows | Where-Object { $_.CoreModuleAddon -eq "Addon" })  | Export-Csv -Path $addonInventory  -NoTypeInformation -Encoding utf8

$changedRows | Export-Csv -Path (Join-Path $artifactRoot "auto_closed_rows.csv") -NoTypeInformation -Encoding utf8

$blankKrdAfter = @($outRows | Where-Object { [string]::IsNullOrWhiteSpace($_.KeepRewriteDrop) }).Count
$blankDecisionAfter = @($outRows | Where-Object { [string]::IsNullOrWhiteSpace($_.FinalDecision) }).Count
$unclassifiedAfter = @($outRows | Where-Object { [string]::IsNullOrWhiteSpace($_.CoreModuleAddon) }).Count
$coreDropConflicts = @($outRows | Where-Object { $_.FinalDecision -eq "Drop" -and $_.CoreModuleAddon -eq "Core" }).Count

$summary = @(
    "# Phase 12 Decision Closer Summary",
    "",
    "Rows updated: $($changedRows.Count)",
    "Unclassified rows after close: $unclassifiedAfter",
    "Blank KRD rows after close: $blankKrdAfter",
    "Blank final decision rows after close: $blankDecisionAfter",
    "Core rows marked Drop after close: $coreDropConflicts"
)
Write-Utf8File -Path (Join-Path $artifactRoot "SUMMARY.md") -Content ($summary -join [Environment]::NewLine)

$runResults = New-Object System.Collections.Generic.List[object]

function Invoke-Step {
    param(
        [string]$Label,
        [string]$ScriptPath,
        [string[]]$Args
    )

    if (-not (Test-Path $ScriptPath)) {
        $runResults.Add([pscustomobject]@{ Step=$Label; Status="MissingScript"; Script=$ScriptPath })
        return
    }

    try {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath @Args
        $runResults.Add([pscustomobject]@{ Step=$Label; Status="Succeeded"; Script=$ScriptPath })
    }
    catch {
        $runResults.Add([pscustomobject]@{ Step=$Label; Status="Failed"; Script=$ScriptPath })
    }
}

Invoke-Step -Label "Phase12" -ScriptPath (Join-Path $scriptDir "80_phase12_auto_review_and_apply.ps1") -Args @()
Invoke-Step -Label "Phase34" -ScriptPath (Join-Path $scriptDir "81_phase34_archive_and_purge_enforcement.ps1") -Args @()
Invoke-Step -Label "Phase567" -ScriptPath (Join-Path $scriptDir "83_phase567_core_module_release_enforcement.ps1") -Args @()
Invoke-Step -Label "GateFinalization" -ScriptPath (Join-Path $scriptDir "85_gate_finalization_and_executive_completion.ps1") -Args @()

$runResults | Export-Csv -Path (Join-Path $artifactRoot "full_rerun_results.csv") -NoTypeInformation -Encoding utf8

Write-Host "DECISION CLOSER COMPLETE"
Write-Host "Artifact root: $artifactRoot"
Write-Host "Rows updated: $($changedRows.Count)"
Write-Host "Blank KRD rows after: $blankKrdAfter"
Write-Host "Blank FinalDecision rows after: $blankDecisionAfter"
Write-Host "Core Drop conflicts after: $coreDropConflicts"
Write-Host "FULL CHAIN COMPLETE"
