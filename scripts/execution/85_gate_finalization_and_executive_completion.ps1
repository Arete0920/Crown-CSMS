param(
    [switch]$OpenFiles
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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

function Get-LatestArtifactDir {
    param([string]$BasePath)
    if (-not (Test-Path $BasePath)) { return $null }
    return Get-ChildItem -Path $BasePath -Directory | Sort-Object Name -Descending | Select-Object -First 1
}

function Read-CsvSafe {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return @() }
    return @(Import-Csv $Path)
}

function ConvertTo-BoolStrict {
    param($Value)
    $s = [string]$Value
    if ($s -match '^(?i:true|1|yes|y)$') { return $true }
    return $false
}

function Get-ControlPaths {
    param([string]$Root)

    $binderRoot = Join-Path $Root "docs\Crown_Master_Binder"
    $opsRoot    = Join-Path $binderRoot "03_Operations_and_Delivery"
    $invRoot    = Join-Path $binderRoot "04_Inventory_Keep_Rewrite_Drop"
    $auditRoot  = Join-Path $Root "audit-artifacts"

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

function Get-GateRows {
    param([string]$GateRegister)
    return [System.Collections.Generic.List[object]]@(Import-Csv $GateRegister)
}

function Save-GateRows {
    param(
        [System.Collections.Generic.List[object]]$Rows,
        [string]$GateRegister
    )
    $Rows | Export-Csv -Path $GateRegister -NoTypeInformation -Encoding utf8
}

function Get-ScoreRows {
    param([string]$Scorecard)
    return [System.Collections.Generic.List[object]]@(Import-Csv $Scorecard)
}

function Save-ScoreRows {
    param(
        [System.Collections.Generic.List[object]]$Rows,
        [string]$Scorecard
    )
    $Rows | Export-Csv -Path $Scorecard -NoTypeInformation -Encoding utf8
}

function Get-RiskRows {
    param([string]$RiskRegister)
    return [System.Collections.Generic.List[object]]@(Import-Csv $RiskRegister)
}

function Save-RiskRows {
    param(
        [System.Collections.Generic.List[object]]$Rows,
        [string]$RiskRegister
    )
    $Rows | Export-Csv -Path $RiskRegister -NoTypeInformation -Encoding utf8
}

function Upsert-Risk {
    param(
        [System.Collections.Generic.List[object]]$RiskRows,
        [string]$RiskID,
        [string]$Phase,
        [string]$Risk,
        [string]$Owner,
        [string]$Severity,
        [string]$Probability,
        [string]$Mitigation,
        [string]$GateImpact,
        [string]$Status,
        [string]$Notes
    )

    $existing = $null
    foreach ($r in $RiskRows) {
        if ($r.RiskID -eq $RiskID) {
            $existing = $r
            break
        }
    }

    if ($existing) {
        $existing.Phase = $Phase
        $existing.Risk = $Risk
        $existing.Owner = $Owner
        $existing.Severity = $Severity
        $existing.Probability = $Probability
        $existing.Mitigation = $Mitigation
        $existing.GateImpact = $GateImpact
        $existing.Status = $Status
        $existing.Notes = $Notes
    }
    else {
        $RiskRows.Add([pscustomobject]@{
            RiskID      = $RiskID
            Phase       = $Phase
            Risk        = $Risk
            Owner       = $Owner
            Severity    = $Severity
            Probability = $Probability
            Mitigation  = $Mitigation
            GateImpact  = $GateImpact
            Status      = $Status
            Notes       = $Notes
        })
    }
}

function Set-GateDecision {
    param(
        [System.Collections.Generic.List[object]]$GateRows,
        [string]$GateID,
        [string]$Status,
        [string]$DecisionBy,
        [string]$Notes
    )

    foreach ($g in $GateRows) {
        if ($g.GateID -eq $GateID) {
            $g.Status = $Status
            $g.DecisionDate = (Get-Date -Format "yyyy-MM-dd")
            $g.DecisionBy = $DecisionBy
            $g.Notes = $Notes
            return
        }
    }

    throw "Gate ID not found: $GateID"
}

function Set-PhaseScore {
    param(
        [System.Collections.Generic.List[object]]$ScoreRows,
        [string]$Phase,
        [int]$Planned,
        [int]$Completed,
        [int]$Blocked,
        [int]$AtRisk,
        [int]$DecisionNeeded,
        [string]$GateStatus,
        [string]$Notes
    )

    foreach ($r in $ScoreRows) {
        if ($r.Phase -eq $Phase) {
            $r.Planned = [string]$Planned
            $r.Completed = [string]$Completed
            $r.Blocked = [string]$Blocked
            $r.AtRisk = [string]$AtRisk
            $r.DecisionNeeded = [string]$DecisionNeeded
            $r.GateStatus = $GateStatus
            $r.Notes = $Notes
        }
    }
}

function Test-TextFileForFailureSignals {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return [pscustomobject]@{
            Exists = $false
            HasFailureSignal = $true
            Notes = "FileMissing"
        }
    }

    $text = Get-Content -Raw -Path $Path
    $patterns = @(
        "Traceback",
        "SystemCheckError",
        "CommandError",
        "Error:",
        "ModuleNotFoundError",
        "ImportError",
        "ImproperlyConfigured"
    )

    foreach ($p in $patterns) {
        if ($text -match [regex]::Escape($p)) {
            return [pscustomobject]@{
                Exists = $true
                HasFailureSignal = $true
                Notes = "Matched:" + $p
            }
        }
    }

    return [pscustomobject]@{
        Exists = $true
        HasFailureSignal = $false
        Notes = "NoFailureSignalDetected"
    }
}

function Evaluate-Phase1 {
    param([object]$Paths)

    $inventory = @(Read-CsvSafe $Paths.MasterInventory)
    $canons = Get-RequiredCanons -BinderRoot $Paths.BinderRoot

    $canonMatrix = foreach ($c in $canons) {
        [pscustomobject]@{
            Canon = Split-Path $c -Leaf
            Exists = Test-Path $c
        }
    }

    $canonMissing = @($canonMatrix | Where-Object { $_.Exists -eq $false })
    $unclassified = @($inventory | Where-Object { [string]::IsNullOrWhiteSpace($_.CoreModuleAddon) })
    $blankKrd = @($inventory | Where-Object { [string]::IsNullOrWhiteSpace($_.KeepRewriteDrop) })

    return [pscustomobject]@{
        InventoryCount    = $inventory.Count
        CanonMissingCount = $canonMissing.Count
        UnclassifiedCount = $unclassified.Count
        BlankKrdCount     = $blankKrd.Count
        Approved          = ($inventory.Count -gt 0 -and $canonMissing.Count -eq 0 -and $unclassified.Count -eq 0 -and $blankKrd.Count -eq 0)
        Notes             = "Inventory=" + $inventory.Count + ";CanonMissing=" + $canonMissing.Count + ";Unclassified=" + $unclassified.Count + ";BlankKRD=" + $blankKrd.Count
    }
}

function Evaluate-Phase2 {
    param([object]$Paths, [bool]$Phase1Approved)

    $inventory = @(Read-CsvSafe $Paths.MasterInventory)

    $blankDecision = @($inventory | Where-Object { [string]::IsNullOrWhiteSpace($_.FinalDecision) })
    $conflicts = @($inventory | Where-Object {
        ($_.Notes -match "CoreDropConflict") -or ($_.FinalDecision -eq "Drop" -and $_.CoreModuleAddon -eq "Core")
    })

    return [pscustomobject]@{
        BlankDecisionCount = $blankDecision.Count
        ConflictCount      = $conflicts.Count
        Approved           = ($Phase1Approved -and $blankDecision.Count -eq 0 -and $conflicts.Count -eq 0)
        Notes              = "Phase1Approved=" + $Phase1Approved + ";BlankDecision=" + $blankDecision.Count + ";Conflicts=" + $conflicts.Count
    }
}

function Evaluate-Phase3 {
    param([object]$Paths, [bool]$Phase2Approved)

    $latest = Get-LatestArtifactDir -BasePath (Join-Path $Paths.AuditRoot "phase3_archive_and_purge_enforcement")
    if (-not $latest) {
        return [pscustomobject]@{
            ArtifactPath = ""
            RestorePassCount = 0
            RestoreFailCount = 1
            Approved = $false
            Notes = "Phase2Approved=" + $Phase2Approved + ";ArtifactMissing=True"
        }
    }

    $restore = @(Read-CsvSafe (Join-Path $latest.FullName "restore_confidence_checklist.csv"))
    $passCount = @($restore | Where-Object { ConvertTo-BoolStrict $_.Pass }).Count
    $failCount = @($restore | Where-Object { -not (ConvertTo-BoolStrict $_.Pass) }).Count

    return [pscustomobject]@{
        ArtifactPath      = $latest.FullName
        RestorePassCount  = $passCount
        RestoreFailCount  = $failCount
        Approved          = ($Phase2Approved -and $restore.Count -gt 0 -and $failCount -eq 0)
        Notes             = "Phase2Approved=" + $Phase2Approved + ";RestoreChecks=" + $restore.Count + ";RestoreFails=" + $failCount
    }
}

function Evaluate-Phase4 {
    param([object]$Paths, [bool]$Phase3Approved)

    $latest = Get-LatestArtifactDir -BasePath (Join-Path $Paths.AuditRoot "phase4_purge_enforcement")
    if (-not $latest) {
        return [pscustomobject]@{
            ArtifactPath = ""
            CandidateCount = 0
            DeletedCount = 0
            FailCount = 1
            BootstrapMissing = 1
            Approved = $false
            Notes = "Phase3Approved=" + $Phase3Approved + ";ArtifactMissing=True"
        }
    }

    $ledger = @(Read-CsvSafe (Join-Path $latest.FullName "purge_ledger.csv"))
    $manifest = @(Read-CsvSafe (Join-Path $latest.FullName "clean_bootstrap_manifest.csv"))

    $failCount = @($ledger | Where-Object {
        $_.Result -in @("DeleteFailed","BlockedGate3NotApproved","DryRunOnly")
    }).Count

    $candidateCount = $ledger.Count
    $deletedCount = @($ledger | Where-Object { $_.Result -eq "Deleted" }).Count
    $protectedBlocks = @($ledger | Where-Object { $_.Result -eq "BlockedProtectedPath" }).Count
    $missingCount = @($ledger | Where-Object { $_.Result -eq "MissingFromDisk" }).Count
    $bootstrapMissing = @($manifest | Where-Object { -not (ConvertTo-BoolStrict $_.Exists) }).Count

    $approve =
        $Phase3Approved -and
        $bootstrapMissing -eq 0 -and
        (
            $candidateCount -eq 0 -or
            ($failCount -eq 0 -and ($deletedCount + $protectedBlocks + $missingCount -eq $candidateCount))
        )

    return [pscustomobject]@{
        ArtifactPath      = $latest.FullName
        CandidateCount    = $candidateCount
        DeletedCount      = $deletedCount
        FailCount         = $failCount
        BootstrapMissing  = $bootstrapMissing
        Approved          = $approve
        Notes             = "Phase3Approved=" + $Phase3Approved + ";Candidates=" + $candidateCount + ";Deleted=" + $deletedCount + ";FailCount=" + $failCount + ";BootstrapMissing=" + $bootstrapMissing
    }
}

function Evaluate-Phase5 {
    param([object]$Paths, [bool]$Phase4Approved)

    $latest = Get-LatestArtifactDir -BasePath (Join-Path $Paths.AuditRoot "phase5_core_build_enforcement")
    if (-not $latest) {
        return [pscustomobject]@{
            ArtifactPath = ""
            GapCount = 1
            DjangoOk = $false
            MigrationsOk = $false
            Approved = $false
            Notes = "Phase4Approved=" + $Phase4Approved + ";ArtifactMissing=True"
        }
    }

    $gaps = @(Read-CsvSafe (Join-Path $latest.FullName "core_gaps.csv"))
    $django = Test-TextFileForFailureSignals -Path (Join-Path $latest.FullName "django_check.txt")
    $migrations = Test-TextFileForFailureSignals -Path (Join-Path $latest.FullName "django_showmigrations.txt")

    $approve = ($Phase4Approved -and $gaps.Count -eq 0 -and -not $django.HasFailureSignal -and -not $migrations.HasFailureSignal)

    return [pscustomobject]@{
        ArtifactPath   = $latest.FullName
        GapCount       = $gaps.Count
        DjangoOk       = (-not $django.HasFailureSignal)
        MigrationsOk   = (-not $migrations.HasFailureSignal)
        Approved       = $approve
        Notes          = "Phase4Approved=" + $Phase4Approved + ";CoreGaps=" + $gaps.Count + ";DjangoOk=" + (-not $django.HasFailureSignal) + ";MigrationsOk=" + (-not $migrations.HasFailureSignal)
    }
}

function Evaluate-Phase6 {
    param([object]$Paths, [bool]$Phase5Approved)

    $latest = Get-LatestArtifactDir -BasePath (Join-Path $Paths.AuditRoot "phase6_first_wave_module_enforcement")
    if (-not $latest) {
        return [pscustomobject]@{
            ArtifactPath = ""
            ModuleGapCount = 1
            IntegrationHitCount = 0
            Approved = $false
            Notes = "Phase5Approved=" + $Phase5Approved + ";ArtifactMissing=True"
        }
    }

    $gaps = @(Read-CsvSafe (Join-Path $latest.FullName "module_gaps.csv"))
    $integration = @(Read-CsvSafe (Join-Path $latest.FullName "module_integration_control_hits.csv"))

    $approve = ($Phase5Approved -and $gaps.Count -eq 0 -and $integration.Count -gt 0)

    return [pscustomobject]@{
        ArtifactPath         = $latest.FullName
        ModuleGapCount       = $gaps.Count
        IntegrationHitCount  = $integration.Count
        Approved             = $approve
        Notes                = "Phase5Approved=" + $Phase5Approved + ";ModuleGaps=" + $gaps.Count + ";IntegrationHits=" + $integration.Count
    }
}

function Evaluate-Phase7 {
    param([object]$Paths, [bool]$Phase6Approved)

    $latest = Get-LatestArtifactDir -BasePath (Join-Path $Paths.AuditRoot "phase7_hardening_release_enforcement")
    if (-not $latest) {
        return [pscustomobject]@{
            ArtifactPath = ""
            FailedCheckCount = 1
            DjangoDeployOk = $false
            Approved = $false
            Notes = "Phase6Approved=" + $Phase6Approved + ";ArtifactMissing=True"
        }
    }

    $checklist = @(Read-CsvSafe (Join-Path $latest.FullName "release_readiness_checklist.csv"))
    $failedChecks = @($checklist | Where-Object { -not (ConvertTo-BoolStrict $_.Pass) }).Count
    $djangoDeploy = Test-TextFileForFailureSignals -Path (Join-Path $latest.FullName "django_check_deploy.txt")

    $approve = ($Phase6Approved -and $checklist.Count -gt 0 -and $failedChecks -eq 0 -and -not $djangoDeploy.HasFailureSignal)

    return [pscustomobject]@{
        ArtifactPath       = $latest.FullName
        FailedCheckCount   = $failedChecks
        DjangoDeployOk     = (-not $djangoDeploy.HasFailureSignal)
        Approved           = $approve
        Notes              = "Phase6Approved=" + $Phase6Approved + ";FailedChecks=" + $failedChecks + ";DjangoDeployOk=" + (-not $djangoDeploy.HasFailureSignal)
    }
}

$root = Get-RepoRoot
Set-Location $root

$paths = Get-ControlPaths -Root $root
$gateRows = Get-GateRows -GateRegister $paths.GateRegister
$scoreRows = Get-ScoreRows -Scorecard $paths.Scorecard
$riskRows = Get-RiskRows -RiskRegister $paths.RiskRegister

$artifactRoot = New-ArtifactRoot -AuditRoot $paths.AuditRoot -Slug "gate_finalization_and_executive_completion"

$p1 = Evaluate-Phase1 -Paths $paths
$p2 = Evaluate-Phase2 -Paths $paths -Phase1Approved $p1.Approved
$p3 = Evaluate-Phase3 -Paths $paths -Phase2Approved $p2.Approved
$p4 = Evaluate-Phase4 -Paths $paths -Phase3Approved $p3.Approved
$p5 = Evaluate-Phase5 -Paths $paths -Phase4Approved $p4.Approved
$p6 = Evaluate-Phase6 -Paths $paths -Phase5Approved $p5.Approved
$p7 = Evaluate-Phase7 -Paths $paths -Phase6Approved $p6.Approved

$decisionRows = @(
    [pscustomobject]@{ GateID="G-001"; Phase="Phase 1"; Status=$(if ($p1.Approved) { "Approved" } else { "Rework Required" }); Notes=$p1.Notes; Evidence=$paths.MasterInventory }
    [pscustomobject]@{ GateID="G-002"; Phase="Phase 2"; Status=$(if ($p2.Approved) { "Approved" } else { "Rework Required" }); Notes=$p2.Notes; Evidence=$paths.MasterInventory }
    [pscustomobject]@{ GateID="G-003"; Phase="Phase 3"; Status=$(if ($p3.Approved) { "Approved" } else { "Rework Required" }); Notes=$p3.Notes; Evidence=$p3.ArtifactPath }
    [pscustomobject]@{ GateID="G-004"; Phase="Phase 4"; Status=$(if ($p4.Approved) { "Approved" } else { "Rework Required" }); Notes=$p4.Notes; Evidence=$p4.ArtifactPath }
    [pscustomobject]@{ GateID="G-005"; Phase="Phase 5"; Status=$(if ($p5.Approved) { "Approved" } else { "Rework Required" }); Notes=$p5.Notes; Evidence=$p5.ArtifactPath }
    [pscustomobject]@{ GateID="G-006"; Phase="Phase 6"; Status=$(if ($p6.Approved) { "Approved" } else { "Rework Required" }); Notes=$p6.Notes; Evidence=$p6.ArtifactPath }
    [pscustomobject]@{ GateID="G-007"; Phase="Phase 7"; Status=$(if ($p7.Approved) { "Approved" } else { "Rework Required" }); Notes=$p7.Notes; Evidence=$p7.ArtifactPath }
)

$decisionRows | Export-Csv -Path (Join-Path $artifactRoot "gate_decision_matrix.csv") -NoTypeInformation -Encoding utf8

Set-GateDecision -GateRows $gateRows -GateID "G-001" -Status $decisionRows[0].Status -DecisionBy "AutoGateCheck" -Notes $decisionRows[0].Notes
Set-GateDecision -GateRows $gateRows -GateID "G-002" -Status $decisionRows[1].Status -DecisionBy "AutoGateCheck" -Notes $decisionRows[1].Notes
Set-GateDecision -GateRows $gateRows -GateID "G-003" -Status $decisionRows[2].Status -DecisionBy "AutoGateCheck" -Notes $decisionRows[2].Notes
Set-GateDecision -GateRows $gateRows -GateID "G-004" -Status $decisionRows[3].Status -DecisionBy "AutoGateCheck" -Notes $decisionRows[3].Notes
Set-GateDecision -GateRows $gateRows -GateID "G-005" -Status $decisionRows[4].Status -DecisionBy "AutoGateCheck" -Notes $decisionRows[4].Notes
Set-GateDecision -GateRows $gateRows -GateID "G-006" -Status $decisionRows[5].Status -DecisionBy "AutoGateCheck" -Notes $decisionRows[5].Notes
Set-GateDecision -GateRows $gateRows -GateID "G-007" -Status $decisionRows[6].Status -DecisionBy "AutoGateCheck" -Notes $decisionRows[6].Notes
Save-GateRows -Rows $gateRows -GateRegister $paths.GateRegister

Set-PhaseScore -ScoreRows $scoreRows -Phase "Phase 1" -Planned $p1.InventoryCount -Completed $(if ($p1.Approved) { $p1.InventoryCount } else { [Math]::Max(0, $p1.InventoryCount - $p1.UnclassifiedCount - $p1.BlankKrdCount - $p1.CanonMissingCount) }) -Blocked $p1.CanonMissingCount -AtRisk $p1.UnclassifiedCount -DecisionNeeded $p1.BlankKrdCount -GateStatus $decisionRows[0].Status -Notes $p1.Notes
Set-PhaseScore -ScoreRows $scoreRows -Phase "Phase 2" -Planned $p1.InventoryCount -Completed $(if ($p2.Approved) { $p1.InventoryCount } else { [Math]::Max(0, $p1.InventoryCount - $p2.BlankDecisionCount - $p2.ConflictCount) }) -Blocked $p2.ConflictCount -AtRisk $p2.BlankDecisionCount -DecisionNeeded $p2.BlankDecisionCount -GateStatus $decisionRows[1].Status -Notes $p2.Notes
Set-PhaseScore -ScoreRows $scoreRows -Phase "Phase 3" -Planned 3 -Completed $(if ($p3.Approved) { 3 } else { [Math]::Max(0, 3 - $p3.RestoreFailCount) }) -Blocked $p3.RestoreFailCount -AtRisk $p3.RestoreFailCount -DecisionNeeded $(if ($p3.Approved) { 0 } else { 1 }) -GateStatus $decisionRows[2].Status -Notes $p3.Notes
Set-PhaseScore -ScoreRows $scoreRows -Phase "Phase 4" -Planned $p4.CandidateCount -Completed $(if ($p4.Approved) { $p4.CandidateCount } else { $p4.DeletedCount }) -Blocked $p4.FailCount -AtRisk $p4.BootstrapMissing -DecisionNeeded $(if ($p4.Approved) { 0 } else { 1 }) -GateStatus $decisionRows[3].Status -Notes $p4.Notes
Set-PhaseScore -ScoreRows $scoreRows -Phase "Phase 5" -Planned 1 -Completed $(if ($p5.Approved) { 1 } else { 0 }) -Blocked $p5.GapCount -AtRisk $(if ($p5.DjangoOk -and $p5.MigrationsOk) { 0 } else { 1 }) -DecisionNeeded $(if ($p5.Approved) { 0 } else { 1 }) -GateStatus $decisionRows[4].Status -Notes $p5.Notes
Set-PhaseScore -ScoreRows $scoreRows -Phase "Phase 6" -Planned 8 -Completed $(if ($p6.Approved) { 8 } else { [Math]::Max(0, 8 - $p6.ModuleGapCount) }) -Blocked $p6.ModuleGapCount -AtRisk $(if ($p6.IntegrationHitCount -gt 0) { 0 } else { 1 }) -DecisionNeeded $(if ($p6.Approved) { 0 } else { 1 }) -GateStatus $decisionRows[5].Status -Notes $p6.Notes
Set-PhaseScore -ScoreRows $scoreRows -Phase "Phase 7" -Planned 1 -Completed $(if ($p7.Approved) { 1 } else { 0 }) -Blocked $p7.FailedCheckCount -AtRisk $(if ($p7.DjangoDeployOk) { 0 } else { 1 }) -DecisionNeeded $(if ($p7.Approved) { 0 } else { 1 }) -GateStatus $decisionRows[6].Status -Notes $p7.Notes
Save-ScoreRows -Rows $scoreRows -Scorecard $paths.Scorecard

Upsert-Risk -RiskRows $riskRows -RiskID "R-801" -Phase "Executive" -Risk "One or more gates not approved" -Owner "TC" -Severity "High" -Probability "High" -Mitigation "Resolve each rework-required gate before completion claim" -GateImpact "Blocks completion" -Status $(if (@($decisionRows | Where-Object { $_.Status -eq "Rework Required" }).Count -gt 0) { "Open" } else { "Closed" }) -Notes ("ReworkGates=" + @($decisionRows | Where-Object { $_.Status -eq "Rework Required" }).Count)
Save-RiskRows -Rows $riskRows -RiskRegister $paths.RiskRegister

$allApproved = (@($decisionRows | Where-Object { $_.Status -eq "Approved" }).Count -eq 7)
$reworkGates = @($decisionRows | Where-Object { $_.Status -eq "Rework Required" })

$execSummaryLines = @(
    "# Executive Completion Summary",
    "",
    "Overall status: " + $(if ($allApproved) { "COMPLETE" } else { "NOT COMPLETE" }),
    "Approved gates: " + @($decisionRows | Where-Object { $_.Status -eq "Approved" }).Count,
    "Rework-required gates: " + $reworkGates.Count,
    "",
    "## Gate results"
)

foreach ($d in $decisionRows) {
    $execSummaryLines += "- $($d.GateID) / $($d.Phase): $($d.Status) | $($d.Notes)"
}

$execSummaryLines += ""
$execSummaryLines += "## Evidence sources"

foreach ($d in $decisionRows) {
    $execSummaryLines += "- $($d.GateID): $($d.Evidence)"
}

if ($reworkGates.Count -gt 0) {
    $execSummaryLines += ""
    $execSummaryLines += "## Immediate blockers"
    foreach ($r in $reworkGates) {
        $execSummaryLines += "- $($r.GateID): $($r.Notes)"
    }
}

Write-Utf8File -Path (Join-Path $artifactRoot "EXECUTIVE_COMPLETION_SUMMARY.md") -Content ($execSummaryLines -join [Environment]::NewLine)

Write-Utf8File -Path (Join-Path $artifactRoot "GATE_FINALIZATION_SUMMARY.md") -Content (@(
    "# Gate Finalization Summary",
    "",
    "Gate register updated: $($paths.GateRegister)",
    "Scorecard updated: $($paths.Scorecard)",
    "Risk register updated: $($paths.RiskRegister)",
    "",
    "Overall status: " + $(if ($allApproved) { "COMPLETE" } else { "NOT COMPLETE" }),
    "Approved gates: " + @($decisionRows | Where-Object { $_.Status -eq "Approved" }).Count,
    "Rework-required gates: " + $reworkGates.Count
) -join [Environment]::NewLine)

Write-Host ""
Write-Host "DONE"
Write-Host "Artifact root: $artifactRoot"
Write-Host "Overall status: $(if ($allApproved) { 'COMPLETE' } else { 'NOT COMPLETE' })"
Write-Host "Approved gates: $(@($decisionRows | Where-Object { $_.Status -eq 'Approved' }).Count)"
Write-Host "Rework-required gates: $($reworkGates.Count)"

if ($OpenFiles) {
    code $paths.GateRegister
    code $paths.Scorecard
    code $paths.RiskRegister
    code (Join-Path $artifactRoot "gate_decision_matrix.csv")
    code (Join-Path $artifactRoot "EXECUTIVE_COMPLETION_SUMMARY.md")
    code (Join-Path $artifactRoot "GATE_FINALIZATION_SUMMARY.md")
}
