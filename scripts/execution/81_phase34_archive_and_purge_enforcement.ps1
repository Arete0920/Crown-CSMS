param(
    [switch]$ExecuteApprovedDrop,
    [switch]$OpenFiles
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    $root = (git rev-parse --show-toplevel 2>$null)
    if (-not $root) { throw "Not inside a git repository." }
    return $root.Trim()
}

function Normalize-Slash {
    param([string]$Path)
    return ($Path -replace "\\","/")
}

function Get-RelativePath {
    param(
        [string]$Root,
        [string]$FullPath
    )

    $prefix = $Root + [IO.Path]::DirectorySeparatorChar
    if ($FullPath.StartsWith($prefix)) {
        return Normalize-Slash ($FullPath.Substring($prefix.Length))
    }
    return Normalize-Slash $FullPath
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

function Merge-Notes {
    param(
        [string]$Existing,
        [string]$Added
    )

    $parts = New-Object System.Collections.Generic.List[string]

    if ($Existing) {
        foreach ($p in ($Existing -split ";")) {
            $t = $p.Trim()
            if ($t) { [void]$parts.Add($t) }
        }
    }

    if ($Added) {
        foreach ($p in ($Added -split ";")) {
            $t = $p.Trim()
            if ($t) { [void]$parts.Add($t) }
        }
    }

    return (($parts | Select-Object -Unique) -join ";")
}

function Get-LatestArtifactDir {
    param([string]$BasePath)

    if (-not (Test-Path $BasePath)) { return $null }

    return Get-ChildItem -Path $BasePath -Directory |
        Sort-Object Name -Descending |
        Select-Object -First 1
}

function Get-ControlPaths {
    param([string]$Root)

    $binderRoot = Join-Path $Root "docs\Crown_Master_Binder"
    $opsRoot    = Join-Path $binderRoot "03_Operations_and_Delivery"
    $invRoot    = Join-Path $binderRoot "04_Inventory_Keep_Rewrite_Drop"
    $auditRoot  = Join-Path $Root "audit-artifacts"

    New-Item -ItemType Directory -Force -Path $binderRoot,$opsRoot,$invRoot,$auditRoot | Out-Null

    $master = Join-Path $invRoot "01_Master_Inventory.csv"
    $core   = Join-Path $invRoot "02_Core_Inventory.csv"
    $module = Join-Path $invRoot "03_Module_Inventory.csv"
    $addon  = Join-Path $invRoot "04_Addon_Inventory.csv"
    $risk   = Join-Path $opsRoot "04_Risk_Register.csv"
    $gate   = Join-Path $opsRoot "09_Phase_Gate_Register.csv"
    $score  = Join-Path $opsRoot "03_Phase_Progress_Scorecard.csv"

    foreach ($req in @($master,$core,$module,$addon,$risk,$gate,$score)) {
        if (-not (Test-Path $req)) {
            throw "Required control file missing: $req"
        }
    }

    return [pscustomobject]@{
        Root            = $Root
        BinderRoot      = $binderRoot
        OpsRoot         = $opsRoot
        InventoryRoot   = $invRoot
        AuditRoot       = $auditRoot
        MasterInventory = $master
        CoreInventory   = $core
        ModuleInventory = $module
        AddonInventory  = $addon
        RiskRegister    = $risk
        GateRegister    = $gate
        Scorecard       = $score
    }
}

function New-ArtifactRoot {
    param(
        [string]$AuditRoot,
        [string]$Slug
    )

    $ts = Get-Date -Format "yyyyMMdd_HHmmss"
    $dir = Join-Path $AuditRoot ($Slug + "\\" + $ts)
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    return $dir
}

function Get-RequiredCanons {
    param([string]$BinderRoot)

    $canonRoot = Join-Path $BinderRoot "02_Architecture_and_Canons"

    return @(
        Join-Path $canonRoot "01_Crown_Core_Canon.md"
        Join-Path $canonRoot "02_Crown_Modules_Canon.md"
        Join-Path $canonRoot "03_Crown_Addons_Canon.md"
        Join-Path $canonRoot "04_SIS_Canon.md"
        Join-Path $canonRoot "05_Auth_RBAC_Canon.md"
        Join-Path $canonRoot "06_Tenant_Isolation_Canon.md"
        Join-Path $canonRoot "07_Naming_Canon.md"
        Join-Path $canonRoot "08_API_Canon.md"
        Join-Path $canonRoot "09_Frontend_Shell_Canon.md"
        Join-Path $canonRoot "10_Definition_of_Done_Canon.md"
    )
}

function Test-Phase12State {
    param([object]$Paths)

    $inventory = Import-Csv $Paths.MasterInventory
    $requiredCanons = Get-RequiredCanons -BinderRoot $Paths.BinderRoot

    $canonMissing = @()
    foreach ($c in $requiredCanons) {
        if (-not (Test-Path $c)) { $canonMissing += $c }
    }

    $unclassified = @($inventory | Where-Object { [string]::IsNullOrWhiteSpace($_.CoreModuleAddon) })
    $blankKrd     = @($inventory | Where-Object { [string]::IsNullOrWhiteSpace($_.KeepRewriteDrop) })
    $blankDecision= @($inventory | Where-Object { [string]::IsNullOrWhiteSpace($_.FinalDecision) })
    $conflicts    = @($inventory | Where-Object { ($_.Notes -match "CoreDropConflict") -or ($_.FinalDecision -eq "Drop" -and $_.CoreModuleAddon -eq "Core") })

    $phase1Ready = ($unclassified.Count -eq 0 -and $blankKrd.Count -eq 0 -and $canonMissing.Count -eq 0)
    $phase2Ready = ($phase1Ready -and $blankDecision.Count -eq 0 -and $conflicts.Count -eq 0)

    return [pscustomobject]@{
        InventoryCount     = @($inventory).Count
        UnclassifiedCount  = $unclassified.Count
        BlankKrdCount      = $blankKrd.Count
        BlankDecisionCount = $blankDecision.Count
        ConflictCount      = $conflicts.Count
        CanonMissingCount  = $canonMissing.Count
        CanonMissing       = $canonMissing
        Phase1Ready        = $phase1Ready
        Phase2Ready        = $phase2Ready
    }
}

function Export-InventorySplits {
    param(
        [object[]]$Rows,
        [object]$Paths
    )

    $Rows | Export-Csv -Path $Paths.MasterInventory -NoTypeInformation -Encoding utf8
    $Rows | Where-Object { $_.CoreModuleAddon -eq "Core" }   | Export-Csv -Path $Paths.CoreInventory   -NoTypeInformation -Encoding utf8
    $Rows | Where-Object { $_.CoreModuleAddon -eq "Module" } | Export-Csv -Path $Paths.ModuleInventory -NoTypeInformation -Encoding utf8
    $Rows | Where-Object { $_.CoreModuleAddon -eq "Addon" }  | Export-Csv -Path $Paths.AddonInventory  -NoTypeInformation -Encoding utf8
}

function Get-GateRows {
    param([string]$GateRegister)
    return @(Import-Csv $GateRegister)
}

function Save-GateRows {
    param(
        [object[]]$Rows,
        [string]$GateRegister
    )
    $Rows | Export-Csv -Path $GateRegister -NoTypeInformation -Encoding utf8
}

function Set-GateStatus {
    param(
        [object[]]$Rows,
        [string]$GateID,
        [string]$Status,
        [string]$Notes,
        [switch]$PreserveApproved
    )

    foreach ($r in $Rows) {
        if ($r.GateID -eq $GateID) {
            if ($PreserveApproved -and $r.Status -eq "Approved") {
                return $Rows
            }
            $r.Status = $Status
            $r.Notes = $Notes
            return $Rows
        }
    }

    return $Rows
}

function Test-ProtectedPath {
    param([string]$RelativePath)

    $p = Normalize-Slash $RelativePath

    if ($p -match "^[.]git/") { return $true }
    if ($p -match "^docs/Crown_Master_Binder/") { return $true }
    if ($p -match "^scripts/execution/") { return $true }
    if ($p -match "^audit-artifacts/") { return $true }
    if ($p -match "^backend/.+/migrations/") { return $true }
    if ($p -match "^backend/manage[.]py$") { return $true }
    if ($p -match "^frontend/package[.]json$") { return $true }
    if ($p -match "^backend/requirements[.]txt$") { return $true }

    return $false
}

function Invoke-Phase3 {
    param(
        [object]$Paths,
        [object]$PhaseState,
        [object[]]$GateRows
    )

    $artifactRoot = New-ArtifactRoot -AuditRoot $Paths.AuditRoot -Slug "phase3_archive_and_purge_enforcement"

    $gitStatusPath = Join-Path $artifactRoot "git_status.txt"
    $gitBranchPath = Join-Path $artifactRoot "git_branch.txt"
    $gitLogPath    = Join-Path $artifactRoot "git_log.txt"
    $gitRemotePath = Join-Path $artifactRoot "git_remote.txt"
    $bundlePath    = Join-Path $artifactRoot "repo.bundle"
    $bundleVerify  = Join-Path $artifactRoot "repo_bundle_verify.txt"
    $archiveZip    = Join-Path $artifactRoot "control_archive.zip"

    git status --short 2>&1 | Set-Content -Path $gitStatusPath -Encoding utf8
    git branch --all 2>&1   | Set-Content -Path $gitBranchPath -Encoding utf8
    git log --oneline -200 2>&1 | Set-Content -Path $gitLogPath -Encoding utf8
    git remote -v 2>&1 | Set-Content -Path $gitRemotePath -Encoding utf8

    try {
        git bundle create "$bundlePath" --all 2>&1 | Out-Null
        git bundle verify "$bundlePath" 2>&1 | Set-Content -Path $bundleVerify -Encoding utf8
    }
    catch {
        $_ | Out-String | Set-Content -Path $bundleVerify -Encoding utf8
    }

    $archiveInputs = @(
        $Paths.BinderRoot
        (Join-Path $Paths.Root "scripts\execution")
        (Join-Path $Paths.Root ".github\workflows")
        $Paths.MasterInventory
        $Paths.CoreInventory
        $Paths.ModuleInventory
        $Paths.AddonInventory
        $Paths.RiskRegister
        $Paths.GateRegister
        $Paths.Scorecard
    ) | Where-Object { Test-Path $_ }

    $archiveInputs = @($archiveInputs)

    if ($archiveInputs.Count -gt 0) {
        Compress-Archive -Path $archiveInputs -DestinationPath $archiveZip -Force
    }

    $envCandidates = Get-ChildItem -Path $Paths.Root -Recurse -File -Force -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -like ".env*" -or
            $_.Name -like "appsettings*.json" -or
            $_.Name -like "settings*.py" -or
            $_.Name -like "docker-compose*.yml" -or
            $_.Name -like "docker-compose*.yaml"
        } |
        Sort-Object FullName |
        ForEach-Object {
            [pscustomobject]@{
                Path      = Get-RelativePath -Root $Paths.Root -FullPath $_.FullName
                Length    = $_.Length
                Modified  = $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            }
        }

    $envCandidates = @($envCandidates)

    $envCandidates | Export-Csv -Path (Join-Path $artifactRoot "environment_candidate_file_index.csv") -NoTypeInformation -Encoding utf8

    $restoreChecklist = @(
        [pscustomobject]@{ Check = "Phase 2 clean"; Pass = $PhaseState.Phase2Ready; Notes = "Phase2Ready=$($PhaseState.Phase2Ready)" }
        [pscustomobject]@{ Check = "Repo bundle exists"; Pass = (Test-Path $bundlePath); Notes = $bundlePath }
        [pscustomobject]@{ Check = "Repo bundle verify file exists"; Pass = (Test-Path $bundleVerify); Notes = $bundleVerify }
        [pscustomobject]@{ Check = "Control archive exists"; Pass = (Test-Path $archiveZip); Notes = $archiveZip }
        [pscustomobject]@{ Check = "Master inventory exists"; Pass = (Test-Path $Paths.MasterInventory); Notes = $Paths.MasterInventory }
        [pscustomobject]@{ Check = "Gate register exists"; Pass = (Test-Path $Paths.GateRegister); Notes = $Paths.GateRegister }
        [pscustomobject]@{ Check = "Risk register exists"; Pass = (Test-Path $Paths.RiskRegister); Notes = $Paths.RiskRegister }
    )

    $restoreChecklist | Export-Csv -Path (Join-Path $artifactRoot "restore_confidence_checklist.csv") -NoTypeInformation -Encoding utf8

    $gate3Ready = ($PhaseState.Phase2Ready -and (Test-Path $bundlePath) -and (Test-Path $archiveZip))
    $gate3Notes = "Phase2Ready=$($PhaseState.Phase2Ready);Bundle=" + (Test-Path $bundlePath) + ";Archive=" + (Test-Path $archiveZip)

    $GateRows = Set-GateStatus -Rows $GateRows -GateID "G-003" -Status ($(if ($gate3Ready) { "Ready for Review" } else { "Working" })) -Notes $gate3Notes -PreserveApproved
    Save-GateRows -Rows $GateRows -GateRegister $Paths.GateRegister

    $summary = @(
        "# Phase 3 Archive and Purge Enforcement Summary",
        "",
        "Phase 2 clean: $($PhaseState.Phase2Ready)",
        "Repo bundle exists: " + (Test-Path $bundlePath),
        "Control archive exists: " + (Test-Path $archiveZip),
        "Environment candidate file count: $($envCandidates.Count)",
        "Gate 3 status: " + $(if ($gate3Ready) { "Ready for Review" } else { "Working" }),
        "",
        "Outputs:",
        "- repo.bundle",
        "- repo_bundle_verify.txt",
        "- control_archive.zip",
        "- environment_candidate_file_index.csv",
        "- restore_confidence_checklist.csv"
    )

    Write-Utf8File -Path (Join-Path $artifactRoot "SUMMARY.md") -Content ($summary -join [Environment]::NewLine)

    return [pscustomobject]@{
        ArtifactRoot = $artifactRoot
        Gate3Ready   = $gate3Ready
    }
}

function Invoke-Phase4 {
    param(
        [object]$Paths,
        [object]$PhaseState,
        [object[]]$GateRows,
        [switch]$ExecuteApprovedDrop
    )

    $artifactRoot = New-ArtifactRoot -AuditRoot $Paths.AuditRoot -Slug "phase4_purge_enforcement"

    $gate3 = $GateRows | Where-Object { $_.GateID -eq "G-003" } | Select-Object -First 1
    $gate3Approved = $false
    if ($gate3 -and $gate3.Status -eq "Approved") { $gate3Approved = $true }

    $inventoryBefore = Import-Csv $Paths.MasterInventory
    $inventoryBefore | Export-Csv -Path (Join-Path $artifactRoot "inventory_before.csv") -NoTypeInformation -Encoding utf8

    $candidates = @($inventoryBefore | Where-Object {
        $_.FinalDecision -eq "Drop" -or $_.KeepRewriteDrop -eq "Drop"
    })

    $purgeLedger = New-Object System.Collections.Generic.List[object]
    $rowsOut = New-Object System.Collections.Generic.List[object]

    foreach ($row in $inventoryBefore) {
        $rowsOut.Add([pscustomobject]@{
            ItemID          = $row.ItemID
            Item            = $row.Item
            Lane            = $row.Lane
            Category        = $row.Category
            Owner           = $row.Owner
            CurrentState    = $row.CurrentState
            CoreModuleAddon = $row.CoreModuleAddon
            KeepRewriteDrop = $row.KeepRewriteDrop
            FinalDecision   = $row.FinalDecision
            Priority        = $row.Priority
            Notes           = $row.Notes
        })
    }

    foreach ($cand in $candidates) {
        $full = Join-Path $Paths.Root ($cand.Item -replace "/","\\")
        $exists = Test-Path $full
        $protected = Test-ProtectedPath -RelativePath $cand.Item
        $action = "DryRun"
        $result = "NotExecuted"

        if (-not $gate3Approved) {
            $result = "BlockedGate3NotApproved"
        }
        elseif (-not $ExecuteApprovedDrop) {
            $result = "DryRunOnly"
        }
        elseif (-not $exists) {
            $result = "MissingFromDisk"
        }
        elseif ($protected) {
            $result = "BlockedProtectedPath"
        }
        else {
            try {
                Remove-Item -LiteralPath $full -Force -Recurse -ErrorAction Stop
                $action = "Delete"
                $result = "Deleted"
            }
            catch {
                $action = "Delete"
                $result = "DeleteFailed"
            }
        }

        $purgeLedger.Add([pscustomobject]@{
            Item            = $cand.Item
            ExistsBefore    = $exists
            Protected       = $protected
            Gate3Approved   = $gate3Approved
            ExecuteApprovedDrop = [bool]$ExecuteApprovedDrop
            Action          = $action
            Result          = $result
        })

        if ($result -eq "Deleted") {
            foreach ($r in $rowsOut) {
                if ($r.ItemID -eq $cand.ItemID) {
                    $r.CurrentState = "PurgedApproved"
                    $r.Notes = Merge-Notes -Existing $r.Notes -Added "Phase4Purged"
                }
            }
        }
    }

    $purgeLedger | Export-Csv -Path (Join-Path $artifactRoot "purge_ledger.csv") -NoTypeInformation -Encoding utf8

    Export-InventorySplits -Rows $rowsOut -Paths $Paths
    $rowsOut | Export-Csv -Path (Join-Path $artifactRoot "inventory_after.csv") -NoTypeInformation -Encoding utf8

    $bootstrapDirs = @(
        "backend\core"
        "backend\apps"
        "frontend\src\core"
        "frontend\src\modules"
        "frontend\src\shell"
        "docs\Crown_Master_Binder"
        "scripts\execution"
    )

    $bootstrapManifest = foreach ($dir in $bootstrapDirs) {
        $full = Join-Path $Paths.Root $dir
        if (-not (Test-Path $full)) {
            New-Item -ItemType Directory -Force -Path $full | Out-Null
        }

        [pscustomobject]@{
            Directory = $dir
            Exists    = Test-Path $full
        }
    }

    $bootstrapManifest | Export-Csv -Path (Join-Path $artifactRoot "clean_bootstrap_manifest.csv") -NoTypeInformation -Encoding utf8

    $deletedCount = @($purgeLedger | Where-Object { $_.Result -eq "Deleted" }).Count
    $failedCount = @($purgeLedger | Where-Object { $_.Result -eq "DeleteFailed" }).Count
    $blockedCount = @($purgeLedger | Where-Object { $_.Result -like "Blocked*" }).Count

    $gate4Ready = ($gate3Approved -and $ExecuteApprovedDrop -and $failedCount -eq 0)
    $gate4Notes = "Gate3Approved=$gate3Approved;ExecuteApprovedDrop=" + [bool]$ExecuteApprovedDrop + ";Deleted=$deletedCount;Failed=$failedCount;Blocked=$blockedCount"

    $GateRows = Set-GateStatus -Rows $GateRows -GateID "G-004" -Status ($(if ($gate4Ready) { "Ready for Review" } else { "Working" })) -Notes $gate4Notes -PreserveApproved
    Save-GateRows -Rows $GateRows -GateRegister $Paths.GateRegister

    $summary = @(
        "# Phase 4 Purge Enforcement Summary",
        "",
        "Gate 3 approved: $gate3Approved",
        "ExecuteApprovedDrop: " + [bool]$ExecuteApprovedDrop,
        "Drop candidates: $($candidates.Count)",
        "Deleted: $deletedCount",
        "Failed: $failedCount",
        "Blocked: $blockedCount",
        "Gate 4 status: " + $(if ($gate4Ready) { "Ready for Review" } else { "Working" }),
        "",
        "Outputs:",
        "- purge_ledger.csv",
        "- inventory_before.csv",
        "- inventory_after.csv",
        "- clean_bootstrap_manifest.csv"
    )

    Write-Utf8File -Path (Join-Path $artifactRoot "SUMMARY.md") -Content ($summary -join [Environment]::NewLine)

    return [pscustomobject]@{
        ArtifactRoot = $artifactRoot
        Gate4Ready   = $gate4Ready
    }
}

$root = Get-RepoRoot
Set-Location $root

$paths = Get-ControlPaths -Root $root
$phaseState = Test-Phase12State -Paths $paths
$gateRows = Get-GateRows -GateRegister $paths.GateRegister

$phase3 = Invoke-Phase3 -Paths $paths -PhaseState $phaseState -GateRows $gateRows

$gateRows = Get-GateRows -GateRegister $paths.GateRegister
$phase4 = Invoke-Phase4 -Paths $paths -PhaseState $phaseState -GateRows $gateRows -ExecuteApprovedDrop:$ExecuteApprovedDrop

$summaryRoot = New-ArtifactRoot -AuditRoot $paths.AuditRoot -Slug "phase34_master_summary"
Write-Utf8File -Path (Join-Path $summaryRoot "SUMMARY.md") -Content (@(
    "# Phase 3 / Phase 4 Master Summary",
    "",
    "Phase 1 clean: $($phaseState.Phase1Ready)",
    "Phase 2 clean: $($phaseState.Phase2Ready)",
    "Unclassified rows: $($phaseState.UnclassifiedCount)",
    "Blank KRD rows: $($phaseState.BlankKrdCount)",
    "Blank final decisions: $($phaseState.BlankDecisionCount)",
    "Conflicts: $($phaseState.ConflictCount)",
    "Missing canons: $($phaseState.CanonMissingCount)",
    "",
    "Phase 3 artifact: $($phase3.ArtifactRoot)",
    "Phase 3 ready: $($phase3.Gate3Ready)",
    "",
    "Phase 4 artifact: $($phase4.ArtifactRoot)",
    "Phase 4 ready: $($phase4.Gate4Ready)",
    "",
    "ExecuteApprovedDrop: " + [bool]$ExecuteApprovedDrop,
    "",
    "Rule:",
    "- Phase 4 destructive action requires Gate 3 = Approved and -ExecuteApprovedDrop."
) -join [Environment]::NewLine)

Write-Host ""
Write-Host "DONE"
Write-Host "Phase 3 artifact: $($phase3.ArtifactRoot)"
Write-Host "Phase 4 artifact: $($phase4.ArtifactRoot)"
Write-Host "Master summary: $(Join-Path $summaryRoot 'SUMMARY.md')"
Write-Host "Gate 3 ready: $($phase3.Gate3Ready)"
Write-Host "Gate 4 ready: $($phase4.Gate4Ready)"

if ($OpenFiles) {
    code (Join-Path $phase3.ArtifactRoot "SUMMARY.md")
    code (Join-Path $phase3.ArtifactRoot "restore_confidence_checklist.csv")
    code (Join-Path $phase3.ArtifactRoot "environment_candidate_file_index.csv")
    code (Join-Path $phase4.ArtifactRoot "SUMMARY.md")
    code (Join-Path $phase4.ArtifactRoot "purge_ledger.csv")
    code (Join-Path $phase4.ArtifactRoot "clean_bootstrap_manifest.csv")
    code $paths.GateRegister
    code $paths.RiskRegister
    code $paths.MasterInventory
}
