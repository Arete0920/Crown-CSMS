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

    return Get-ChildItem -Path $BasePath -Directory |
        Sort-Object Name -Descending |
        Select-Object -First 1
}

function Ensure-ControlFiles {
    param([string]$Root)

    $binderRoot = Join-Path $Root "docs\Crown_Master_Binder"
    $opsRoot    = Join-Path $binderRoot "03_Operations_and_Delivery"
    $invRoot    = Join-Path $binderRoot "04_Inventory_Keep_Rewrite_Drop"

    New-Item -ItemType Directory -Force -Path $binderRoot,$opsRoot,$invRoot | Out-Null

    $master = Join-Path $invRoot "01_Master_Inventory.csv"
    $core   = Join-Path $invRoot "02_Core_Inventory.csv"
    $module = Join-Path $invRoot "03_Module_Inventory.csv"
    $addon  = Join-Path $invRoot "04_Addon_Inventory.csv"
    $risk   = Join-Path $opsRoot "04_Risk_Register.csv"
    $gate   = Join-Path $opsRoot "09_Phase_Gate_Register.csv"
    $score  = Join-Path $opsRoot "03_Phase_Progress_Scorecard.csv"

    if (-not (Test-Path $master)) {
        "ItemID,Item,Lane,Category,Owner,CurrentState,CoreModuleAddon,KeepRewriteDrop,FinalDecision,Priority,Notes" |
            Set-Content -Path $master -Encoding utf8
    }

    if (-not (Test-Path $core)) {
        "ItemID,Item,Lane,Category,Owner,CurrentState,CoreModuleAddon,KeepRewriteDrop,FinalDecision,Priority,Notes" |
            Set-Content -Path $core -Encoding utf8
    }

    if (-not (Test-Path $module)) {
        "ItemID,Item,Lane,Category,Owner,CurrentState,CoreModuleAddon,KeepRewriteDrop,FinalDecision,Priority,Notes" |
            Set-Content -Path $module -Encoding utf8
    }

    if (-not (Test-Path $addon)) {
        "ItemID,Item,Lane,Category,Owner,CurrentState,CoreModuleAddon,KeepRewriteDrop,FinalDecision,Priority,Notes" |
            Set-Content -Path $addon -Encoding utf8
    }

    if (-not (Test-Path $risk)) {
        @"
RiskID,Phase,Risk,Owner,Severity,Probability,Mitigation,GateImpact,Status,Notes
R-001,Phase 1,Inventory incomplete before classification,Dev 5,High,Medium,No classification until master inventory is materially complete,Blocks Gate 1,Open,
R-002,Phase 2,Shadow truth reintroduced by modules,Dev 1,High,Medium,Enforce core truth and API canon,Blocks Gate 2,Open,
R-003,Phase 2,Classification conflicts remain unresolved,TC,High,Medium,Resolve conflicts before approval,Blocks Gate 2,Open,
"@ | Set-Content -Path $risk -Encoding utf8
    }

    if (-not (Test-Path $gate)) {
        @"
GateID,Phase,GateName,Owner,EntryCriteria,ExitCriteria,Status,DecisionDate,DecisionBy,Notes
G-001,Phase 1,Inventory and Canon Lock,TC,Inventory underway and canon drafts started,Inventory materially complete and canon drafts ready,Not Started,,,
G-002,Phase 2,Classification and Approval,TC,Gate 1 approved,Keep/Rewrite/Drop and canon approvals complete,Not Started,,,
"@ | Set-Content -Path $gate -Encoding utf8
    }

    if (-not (Test-Path $score)) {
        @"
Phase,Stage,Owner,Planned,Completed,Blocked,AtRisk,DecisionNeeded,GateStatus,Notes
Phase 1,Stage A - Draft,Dev 1,0,0,0,0,0,Not Started,
Phase 1,Stage B - Working,Dev 2,0,0,0,0,0,Not Started,
Phase 1,Stage C - Evidence Complete,Dev 5,0,0,0,0,0,Not Started,
Phase 1,Stage D - Gate Review,TC,0,0,0,0,0,Not Started,
Phase 2,Stage A - Draft,Dev 1,0,0,0,0,0,Not Started,
Phase 2,Stage B - Working,Dev 3,0,0,0,0,0,Not Started,
Phase 2,Stage C - Evidence Complete,Dev 5,0,0,0,0,0,Not Started,
Phase 2,Stage D - Gate Review,TC,0,0,0,0,0,Not Started,
"@ | Set-Content -Path $score -Encoding utf8
    }

    return [pscustomobject]@{
        BinderRoot      = $binderRoot
        OpsRoot         = $opsRoot
        InventoryRoot   = $invRoot
        MasterInventory = $master
        CoreInventory   = $core
        ModuleInventory = $module
        AddonInventory  = $addon
        RiskRegister    = $risk
        GateRegister    = $gate
        Scorecard       = $score
    }
}

function Guess-Lane {
    param([string]$Path)

    $p = $Path.ToLowerInvariant()

    if ($p -match "^backend/") { return "Backend" }
    if ($p -match "^frontend/") { return "Frontend" }
    if ($p -match "^docs/") { return "Docs" }
    if ($p -match "^scripts/") { return "Scripts" }
    if ($p -match "^[.]github/") { return "GitHub" }
    if ($p -match "^tests?/") { return "Tests" }
    if ($p -match "docker|compose|container|azure|terraform|iac|deploy") { return "Infra" }
    return "Root"
}

function Guess-Category {
    param([string]$Path)

    $p = $Path.ToLowerInvariant()

    if ($p -match "requirements|package-lock|package[.]json|poetry|pipfile|yarn[.]lock|pnpm-lock") { return "Dependency" }
    if ($p -match "/migrations/|\\migrations\\") { return "Migration" }
    if ($p -match "[.]py$") { return "Python" }
    if ($p -match "[.](ts|tsx|js|jsx)$") { return "FrontendCode" }
    if ($p -match "[.](md|txt|rst)$") { return "Document" }
    if ($p -match "[.](yml|yaml|json|ini|cfg|toml)$") { return "Config" }
    if ($p -match "[.](ps1|sh|bat)$") { return "Script" }
    if ($p -match "test|spec") { return "Test" }
    if ($p -match "[.](png|jpg|jpeg|svg|gif|ico|webp)$") { return "Asset" }
    return "Other"
}

function Guess-CoreModuleAddon {
    param([string]$Path)

    $p = $Path.ToLowerInvariant()

    if ($p -match "spiritual|outreach|service|compass|pd[_-]?hub|board|portrait|chaplain|mission") { return "Addon" }
    if ($p -match "admission|enroll|billing|tuition|payment|portal|communication|transport|food|nurse|athletic|activity") { return "Module" }
    if ($p -match "auth|rbac|tenant|core|household|student|staff|academic|transcript|attendance|grade|school|term|year|section|roster|audit") { return "Core" }
    if ($p -match "^backend/" -or $p -match "^frontend/" -or $p -match "^docs/") { return "Core" }
    return ""
}

function Guess-Owner {
    param(
        [string]$Lane,
        [string]$CoreModuleAddon,
        [string]$Path
    )

    $p = $Path.ToLowerInvariant()

    if ($Lane -eq "Frontend") { return "Dev 4" }
    if ($Lane -eq "GitHub" -or $Lane -eq "Infra") { return "Dev 5" }
    if ($CoreModuleAddon -eq "Addon" -or $CoreModuleAddon -eq "Module") { return "Dev 3" }
    if ($p -match "student|household|guardian|staff|academic|attendance|grade|transcript|enrollment|term|year|section|roster") { return "Dev 2" }
    if ($p -match "auth|rbac|tenant|core|middleware|security|api|permission|audit") { return "Dev 1" }
    if ($Lane -eq "Docs" -or $Lane -eq "Scripts") { return "Dev 5" }
    return "Dev 5"
}

function Guess-State {
    param(
        [string]$Path,
        [int64]$Size,
        [datetime]$LastWrite
    )

    $p = $Path.ToLowerInvariant()
    $ageDays = [int]((Get-Date) - $LastWrite).TotalDays

    if ($p -match "/[.]history/|^node_modules/|/node_modules/|^dist/|/dist/|^build/|/build/|^coverage/|/coverage/|__pycache__|[.]pytest_cache") {
        return "GeneratedOrStale"
    }

    if ($Size -eq 0) { return "Empty" }
    if ($ageDays -gt 180) { return "ReviewAged" }
    return "InventoryNeeded"
}

function Guess-KeepRewriteDrop {
    param(
        [string]$Path,
        [string]$Category,
        [string]$CurrentState
    )

    $p = $Path.ToLowerInvariant()

    if ($p -match "/[.]history/|^node_modules/|/node_modules/|^dist/|/dist/|^build/|/build/|^coverage/|/coverage/|__pycache__|[.]pytest_cache") {
        return "Drop"
    }

    if ($CurrentState -eq "Empty") { return "Rewrite" }

    if ($Category -in @("Migration","Dependency","Config","Test")) { return "Keep" }

    if ($p -match "^docs/crown_master_binder/") { return "Keep" }

    if ($CurrentState -eq "ReviewAged" -and $Category -eq "Document") { return "Rewrite" }

    return ""
}

function Recommend-FinalDecision {
    param(
        [string]$Item,
        [string]$Lane,
        [string]$Category,
        [string]$CurrentState,
        [string]$KeepRewriteDrop,
        [string]$CoreModuleAddon
    )

    $p = $Item.ToLowerInvariant()

    if ($p -match "^docs/crown_master_binder/" -or $p -match "^scripts/execution/") {
        return [pscustomobject]@{ Decision = "Keep"; Confidence = "High"; Rule = "ControlledAuthorityPath" }
    }

    if ($Category -in @("Migration","Dependency","Config","Test")) {
        return [pscustomobject]@{ Decision = "Keep"; Confidence = "High"; Rule = "ControlledInfraOrValidationArtifact" }
    }

    if ($p -match "/[.]history/|^node_modules/|/node_modules/|^dist/|/dist/|^build/|/build/|^coverage/|/coverage/|__pycache__|[.]pytest_cache") {
        return [pscustomobject]@{ Decision = "Drop"; Confidence = "High"; Rule = "GeneratedOrStalePath" }
    }

    if ($CurrentState -eq "Empty") {
        return [pscustomobject]@{ Decision = "Rewrite"; Confidence = "High"; Rule = "EmptyFile" }
    }

    if ($CurrentState -eq "ReviewAged" -and $Category -eq "Document" -and $Lane -ne "Docs") {
        return [pscustomobject]@{ Decision = "Rewrite"; Confidence = "Medium"; Rule = "AgedNonBinderDocument" }
    }

    if ($KeepRewriteDrop -eq "Drop" -and $CoreModuleAddon -eq "" -and $Lane -in @("Root","Scripts")) {
        return [pscustomobject]@{ Decision = "Drop"; Confidence = "Medium"; Rule = "NonCoreDropCandidate" }
    }

    return [pscustomobject]@{ Decision = ""; Confidence = ""; Rule = "" }
}

function Update-GateRow {
    param(
        [object[]]$Rows,
        [string]$Phase,
        [string]$Status,
        [string]$Notes
    )

    foreach ($r in $Rows) {
        if ($r.Phase -eq $Phase) {
            $r.Status = $Status
            $r.Notes = $Notes
        }
    }

    return $Rows
}

function Update-ScorecardRows {
    param(
        [object[]]$Rows,
        [string]$Phase,
        [int]$Planned,
        [int]$Completed,
        [int]$Blocked,
        [int]$AtRisk,
        [int]$DecisionNeeded,
        [string]$GateStatus,
        [string]$Notes
    )

    foreach ($r in $Rows) {
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

    return $Rows
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

$root = Get-RepoRoot
Set-Location $root

$paths = Ensure-ControlFiles -Root $root

if (-not (Test-Path $paths.MasterInventory)) {
    throw "Master inventory not found: $($paths.MasterInventory)"
}

$artifactRoot = Join-Path $root ("audit-artifacts\phase12_auto_review\" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force -Path $artifactRoot | Out-Null

$phase1Latest = Get-LatestArtifactDir -BasePath (Join-Path $root "audit-artifacts\phase1_inventory_and_canon_lock")
$phase2Latest = Get-LatestArtifactDir -BasePath (Join-Path $root "audit-artifacts\phase2_classification_and_approval")

$requiredCanons = @(
    "01_Crown_Core_Canon.md",
    "02_Crown_Modules_Canon.md",
    "03_Crown_Addons_Canon.md",
    "04_SIS_Canon.md",
    "05_Auth_RBAC_Canon.md",
    "06_Tenant_Isolation_Canon.md",
    "07_Naming_Canon.md",
    "08_API_Canon.md",
    "09_Frontend_Shell_Canon.md",
    "10_Definition_of_Done_Canon.md"
)

$canonMatrix = foreach ($canon in $requiredCanons) {
    $full = Join-Path $paths.BinderRoot ("02_Architecture_and_Canons\" + $canon)
    [pscustomobject]@{
        Canon  = $canon
        Exists = Test-Path $full
        Status = if (Test-Path $full) { "Present" } else { "Missing" }
    }
}
$canonMatrix | Export-Csv -Path (Join-Path $artifactRoot "canon_presence_matrix.csv") -NoTypeInformation -Encoding utf8

$inventory = Import-Csv $paths.MasterInventory
$rowsOut = New-Object System.Collections.Generic.List[object]

$changes = New-Object System.Collections.Generic.List[object]
$reviewQueue = New-Object System.Collections.Generic.List[object]
$conflicts = New-Object System.Collections.Generic.List[object]

foreach ($row in $inventory) {
    $item = $row.Item
    $lane = if ([string]::IsNullOrWhiteSpace($row.Lane)) { Guess-Lane -Path $item } else { $row.Lane }
    $category = if ([string]::IsNullOrWhiteSpace($row.Category)) { Guess-Category -Path $item } else { $row.Category }
    $cma = if ([string]::IsNullOrWhiteSpace($row.CoreModuleAddon)) { Guess-CoreModuleAddon -Path $item } else { $row.CoreModuleAddon }
    $owner = if ([string]::IsNullOrWhiteSpace($row.Owner)) { Guess-Owner -Lane $lane -CoreModuleAddon $cma -Path $item } else { $row.Owner }
    $state = $row.CurrentState
    if ([string]::IsNullOrWhiteSpace($state)) {
        $fullItemPath = Join-Path $root ($item -replace "/","\\")
        if (Test-Path $fullItemPath) {
            $fileInfo = Get-Item $fullItemPath
            $state = Guess-State -Path $item -Size $fileInfo.Length -LastWrite $fileInfo.LastWriteTime
        }
        else {
            $state = "MissingFromDisk"
        }
    }

    $krd = $row.KeepRewriteDrop
    $decision = $row.FinalDecision
    $priority = $row.Priority
    $notes = $row.Notes

    if ([string]::IsNullOrWhiteSpace($krd)) {
        $newKrd = Guess-KeepRewriteDrop -Path $item -Category $category -CurrentState $state
        if ($newKrd) {
            $krd = $newKrd
            $notes = Merge-Notes -Existing $notes -Added ("AutoKRD:" + $newKrd)
        }
    }

    $rec = Recommend-FinalDecision -Item $item -Lane $lane -Category $category -CurrentState $state -KeepRewriteDrop $krd -CoreModuleAddon $cma
    if ([string]::IsNullOrWhiteSpace($decision) -and $rec.Decision) {
        $decision = $rec.Decision
        $notes = Merge-Notes -Existing $notes -Added ("AutoDecision:" + $rec.Decision + ":" + $rec.Confidence + ":" + $rec.Rule)
    }

    if ([string]::IsNullOrWhiteSpace($priority)) {
        $priority =
            if ($cma -eq "Core") { "P0" }
            elseif ($cma -eq "Module") { "P1" }
            elseif ($cma -eq "Addon") { "P2" }
            else { "P3" }
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

    if (
        $row.Lane -ne $lane -or
        $row.Category -ne $category -or
        $row.Owner -ne $owner -or
        $row.CurrentState -ne $state -or
        $row.CoreModuleAddon -ne $cma -or
        $row.KeepRewriteDrop -ne $krd -or
        $row.FinalDecision -ne $decision -or
        $row.Priority -ne $priority -or
        $row.Notes -ne $notes
    ) {
        $changes.Add([pscustomobject]@{
            Item            = $item
            LaneBefore      = $row.Lane
            LaneAfter       = $lane
            CategoryBefore  = $row.Category
            CategoryAfter   = $category
            CMABefore       = $row.CoreModuleAddon
            CMAAfter        = $cma
            KRDBefore       = $row.KeepRewriteDrop
            KRDAfter        = $krd
            DecisionBefore  = $row.FinalDecision
            DecisionAfter   = $decision
            NotesAfter      = $notes
        })
    }

    if ($decision -eq "Drop" -and $cma -eq "Core") {
        $conflicts.Add([pscustomobject]@{
            Item = $item
            Conflict = "CoreMarkedDrop"
            Notes = $notes
        })
    }

    if (
        [string]::IsNullOrWhiteSpace($cma) -or
        [string]::IsNullOrWhiteSpace($krd) -or
        [string]::IsNullOrWhiteSpace($decision)
    ) {
        $reviewQueue.Add([pscustomobject]@{
            Item            = $item
            Lane            = $lane
            Category        = $category
            CoreModuleAddon = $cma
            KeepRewriteDrop = $krd
            FinalDecision   = $decision
            CurrentState    = $state
            Notes           = $notes
        })
    }

    $rowsOut.Add($newRow)
}

$rowsOut | Export-Csv -Path $paths.MasterInventory -NoTypeInformation -Encoding utf8
$rowsOut | Where-Object { $_.CoreModuleAddon -eq "Core" }   | Export-Csv -Path $paths.CoreInventory   -NoTypeInformation -Encoding utf8
$rowsOut | Where-Object { $_.CoreModuleAddon -eq "Module" } | Export-Csv -Path $paths.ModuleInventory -NoTypeInformation -Encoding utf8
$rowsOut | Where-Object { $_.CoreModuleAddon -eq "Addon" }  | Export-Csv -Path $paths.AddonInventory  -NoTypeInformation -Encoding utf8

$changes | Export-Csv -Path (Join-Path $artifactRoot "applied_changes.csv") -NoTypeInformation -Encoding utf8
$reviewQueue | Export-Csv -Path (Join-Path $artifactRoot "remaining_review_queue.csv") -NoTypeInformation -Encoding utf8
$conflicts | Export-Csv -Path (Join-Path $artifactRoot "classification_conflicts.csv") -NoTypeInformation -Encoding utf8

$canonMissingCount = @($canonMatrix | Where-Object { $_.Exists -eq $false }).Count
$unclassifiedCount = @($rowsOut | Where-Object { [string]::IsNullOrWhiteSpace($_.CoreModuleAddon) }).Count
$blankKrdCount = @($rowsOut | Where-Object { [string]::IsNullOrWhiteSpace($_.KeepRewriteDrop) }).Count
$blankDecisionCount = @($rowsOut | Where-Object { [string]::IsNullOrWhiteSpace($_.FinalDecision) }).Count
$conflictCount = $conflicts.Count

$gateRows = [System.Collections.Generic.List[object]]::new()
foreach ($g in (Import-Csv $paths.GateRegister)) { $gateRows.Add($g) }

$phase1Ready = ($unclassifiedCount -eq 0 -and $blankKrdCount -eq 0 -and $canonMissingCount -eq 0)
$phase2Ready = ($unclassifiedCount -eq 0 -and $blankKrdCount -eq 0 -and $blankDecisionCount -eq 0 -and $conflictCount -eq 0 -and $canonMissingCount -eq 0)

$gateRows = Update-GateRow -Rows $gateRows -Phase "Phase 1" -Status ($(if ($phase1Ready) { "Ready for Review" } else { "Working" })) -Notes ("Unclassified=" + $unclassifiedCount + ";BlankKRD=" + $blankKrdCount + ";CanonMissing=" + $canonMissingCount)
$gateRows = Update-GateRow -Rows $gateRows -Phase "Phase 2" -Status ($(if ($phase2Ready) { "Ready for Review" } else { "Working" })) -Notes ("BlankDecision=" + $blankDecisionCount + ";Conflicts=" + $conflictCount + ";CanonMissing=" + $canonMissingCount)

$gateRows | Export-Csv -Path $paths.GateRegister -NoTypeInformation -Encoding utf8

$scoreRows = [System.Collections.Generic.List[object]]::new()
foreach ($s in (Import-Csv $paths.Scorecard)) { $scoreRows.Add($s) }

$phase1Planned = $rowsOut.Count
$phase1Completed = $rowsOut.Count - $unclassifiedCount - $blankKrdCount
$phase1Blocked = $canonMissingCount
$phase1AtRisk = $conflictCount
$phase1DecisionNeeded = $blankDecisionCount

$phase2Planned = $rowsOut.Count
$phase2Completed = $rowsOut.Count - $blankDecisionCount - $conflictCount
$phase2Blocked = $conflictCount
$phase2AtRisk = $blankDecisionCount
$phase2DecisionNeeded = $blankDecisionCount

$scoreRows = Update-ScorecardRows -Rows $scoreRows -Phase "Phase 1" -Planned $phase1Planned -Completed $phase1Completed -Blocked $phase1Blocked -AtRisk $phase1AtRisk -DecisionNeeded $phase1DecisionNeeded -GateStatus ($(if ($phase1Ready) { "Ready for Review" } else { "Working" })) -Notes ("AutoReviewApplied;CanonMissing=" + $canonMissingCount)
$scoreRows = Update-ScorecardRows -Rows $scoreRows -Phase "Phase 2" -Planned $phase2Planned -Completed $phase2Completed -Blocked $phase2Blocked -AtRisk $phase2AtRisk -DecisionNeeded $phase2DecisionNeeded -GateStatus ($(if ($phase2Ready) { "Ready for Review" } else { "Working" })) -Notes ("AutoReviewApplied;Conflicts=" + $conflictCount)

$scoreRows | Export-Csv -Path $paths.Scorecard -NoTypeInformation -Encoding utf8

$riskRows = [System.Collections.Generic.List[object]]::new()
foreach ($r in (Import-Csv $paths.RiskRegister)) { $riskRows.Add($r) }

Upsert-Risk -RiskRows $riskRows -RiskID "R-101" -Phase "Phase 1" -Risk "Unclassified inventory rows remain" -Owner "Dev 5" -Severity "High" -Probability "Medium" -Mitigation "Resolve unclassified rows before Gate 1 review" -GateImpact "Blocks Gate 1" -Status ($(if ($unclassifiedCount -gt 0) { "Open" } else { "Closed" })) -Notes ("Count=" + $unclassifiedCount)
Upsert-Risk -RiskRows $riskRows -RiskID "R-102" -Phase "Phase 1" -Risk "Blank Keep/Rewrite/Drop values remain" -Owner "Dev 5" -Severity "High" -Probability "Medium" -Mitigation "Resolve blank KRD rows before Gate 1 review" -GateImpact "Blocks Gate 1" -Status ($(if ($blankKrdCount -gt 0) { "Open" } else { "Closed" })) -Notes ("Count=" + $blankKrdCount)
Upsert-Risk -RiskRows $riskRows -RiskID "R-201" -Phase "Phase 2" -Risk "Blank final decisions remain" -Owner "TC" -Severity "High" -Probability "Medium" -Mitigation "Resolve remaining decision queue before Gate 2 review" -GateImpact "Blocks Gate 2" -Status ($(if ($blankDecisionCount -gt 0) { "Open" } else { "Closed" })) -Notes ("Count=" + $blankDecisionCount)
Upsert-Risk -RiskRows $riskRows -RiskID "R-202" -Phase "Phase 2" -Risk "Classification conflicts remain" -Owner "TC" -Severity "High" -Probability "Low" -Mitigation "Resolve conflicts before Phase 2 approval" -GateImpact "Blocks Gate 2" -Status ($(if ($conflictCount -gt 0) { "Open" } else { "Closed" })) -Notes ("Count=" + $conflictCount)
Upsert-Risk -RiskRows $riskRows -RiskID "R-203" -Phase "Phase 2" -Risk "Required canons missing" -Owner "Dev 1" -Severity "High" -Probability "Low" -Mitigation "Restore or create missing canon files before review" -GateImpact "Blocks Gate 1 and Gate 2" -Status ($(if ($canonMissingCount -gt 0) { "Open" } else { "Closed" })) -Notes ("Count=" + $canonMissingCount)

$riskRows | Export-Csv -Path $paths.RiskRegister -NoTypeInformation -Encoding utf8

$phase1InputSummary = if ($phase1Latest) { $phase1Latest.FullName } else { "NotFound" }
$phase2InputSummary = if ($phase2Latest) { $phase2Latest.FullName } else { "NotFound" }

$summaryLines = @(
    "# Phase 1 / Phase 2 Auto Review Summary",
    "",
    "Phase 1 latest artifact: $phase1InputSummary",
    "Phase 2 latest artifact: $phase2InputSummary",
    "",
    "Applied changes: $($changes.Count)",
    "Remaining review queue: $($reviewQueue.Count)",
    "Conflicts: $conflictCount",
    "Canon missing: $canonMissingCount",
    "Unclassified rows: $unclassifiedCount",
    "Blank KRD rows: $blankKrdCount",
    "Blank final decision rows: $blankDecisionCount",
    "",
    "Gate 1 status: " + $(if ($phase1Ready) { "Ready for Review" } else { "Working" }),
    "Gate 2 status: " + $(if ($phase2Ready) { "Ready for Review" } else { "Working" }),
    "",
    "Updated files:",
    "- docs/Crown_Master_Binder/04_Inventory_Keep_Rewrite_Drop/01_Master_Inventory.csv",
    "- docs/Crown_Master_Binder/04_Inventory_Keep_Rewrite_Drop/02_Core_Inventory.csv",
    "- docs/Crown_Master_Binder/04_Inventory_Keep_Rewrite_Drop/03_Module_Inventory.csv",
    "- docs/Crown_Master_Binder/04_Inventory_Keep_Rewrite_Drop/04_Addon_Inventory.csv",
    "- docs/Crown_Master_Binder/03_Operations_and_Delivery/04_Risk_Register.csv",
    "- docs/Crown_Master_Binder/03_Operations_and_Delivery/09_Phase_Gate_Register.csv",
    "- docs/Crown_Master_Binder/03_Operations_and_Delivery/03_Phase_Progress_Scorecard.csv"
)

Write-Utf8File -Path (Join-Path $artifactRoot "SUMMARY.md") -Content ($summaryLines -join [Environment]::NewLine)

Write-Utf8File -Path (Join-Path $artifactRoot "PHASE12_GATE_PACKET.md") -Content (@(
    "# Phase 1 / Phase 2 Gate Packet",
    "",
    "## Gate 1",
    "- Status: " + $(if ($phase1Ready) { "Ready for Review" } else { "Working" }),
    "- Unclassified rows: $unclassifiedCount",
    "- Blank Keep/Rewrite/Drop rows: $blankKrdCount",
    "- Missing canons: $canonMissingCount",
    "",
    "## Gate 2",
    "- Status: " + $(if ($phase2Ready) { "Ready for Review" } else { "Working" }),
    "- Blank final decisions: $blankDecisionCount",
    "- Conflicts: $conflictCount",
    "- Missing canons: $canonMissingCount",
    "",
    "## Review files",
    "- applied_changes.csv",
    "- remaining_review_queue.csv",
    "- classification_conflicts.csv",
    "- canon_presence_matrix.csv"
) -join [Environment]::NewLine)

Write-Host ""
Write-Host "DONE"
Write-Host "Artifact root: $artifactRoot"
Write-Host "Applied changes: $($changes.Count)"
Write-Host "Remaining review queue: $($reviewQueue.Count)"
Write-Host "Conflicts: $conflictCount"
Write-Host "Gate 1: $(if ($phase1Ready) { 'Ready for Review' } else { 'Working' })"
Write-Host "Gate 2: $(if ($phase2Ready) { 'Ready for Review' } else { 'Working' })"

if ($OpenFiles) {
    code $paths.MasterInventory
    code $paths.CoreInventory
    code $paths.ModuleInventory
    code $paths.AddonInventory
    code $paths.RiskRegister
    code $paths.GateRegister
    code $paths.Scorecard
    code (Join-Path $artifactRoot "SUMMARY.md")
    code (Join-Path $artifactRoot "remaining_review_queue.csv")
    code (Join-Path $artifactRoot "classification_conflicts.csv")
    code (Join-Path $artifactRoot "canon_presence_matrix.csv")
}
