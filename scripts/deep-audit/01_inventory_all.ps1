param(
  [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

$inv = "docs\audit\inventories"
New-Item -ItemType Directory -Force -Path $inv | Out-Null

function Export-Utf8Csv {
  param(
    [Parameter(Mandatory=$true)]$Rows,
    [Parameter(Mandatory=$true)][string]$Path
  )
  $Rows | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
}

function Get-LayerFromPath([string]$Path) {
  $p = $Path.ToLower()
  if ($p -match 'spiritual|outreach|compass|governance|pd[_\- ]?hub|portrait|chaplain|mission') { return "Add-on" }
  if ($p -match 'admissions|enroll|billing|payment|comms|portal|attendance|schedule|gradebook|athletic|activity|transport|food|nurse|discipline|board') { return "Module" }
  return "Core"
}

function Get-OwnerFromPath([string]$Path) {
  $p = $Path.ToLower()
  if ($p -match 'auth|rbac|tenant|permission|middleware|api|core|release|workflow|deploy') { return "Dev 1 / Dev 5" }
  if ($p -match 'student|household|guardian|faculty|staff|school|academic|roster|transcript|attendance') { return "Dev 2" }
  if ($p -match 'admissions|enroll|billing|payment|comms|transport|food|nurse|activity|athletic|board|discipline') { return "Dev 3" }
  if ($p -match 'frontend|dashboard|wizard|page|component|route|shell|portal') { return "Dev 4" }
  if ($p -match 'test|pytest|workflow|ci|release') { return "Dev 5" }
  return "MUST_ASSIGN"
}

function Get-AssetType([string]$Path) {
  $name = [System.IO.Path]::GetFileName($Path).ToLower()
  $dir = [System.IO.Path]::GetDirectoryName($Path).ToLower()
  if ($dir -match '\\pages\\' -or $name -match 'dashboard') { return "PageOrDashboard" }
  if ($name -match 'wizard|step\d') { return "Wizard" }
  if ($name -match 'views_|api_|viewset|router|urls\.py|serializers?') { return "APIOrView" }
  if ($name -match 'models?\.py') { return "ModelFile" }
  if ($name -match 'services?') { return "ServiceFile" }
  if ($name -match 'test_|_test|spec\.') { return "TestFile" }
  if ($dir -match '\.github\\workflows') { return "WorkflowFile" }
  if ($name -match 'readme|changelog|security|compliance|canon|runbook|guide|report') { return "DocFile" }
  return "File"
}

function Get-ModuleName([string]$Path) {
  $p = $Path.ToLower()
  if ($p -match 'admissions') { return "Admissions" }
  if ($p -match 'reenroll|re-enroll|enrollment') { return "Re-enrollment" }
  if ($p -match 'billing|payment|ledger|finance') { return "Billing / Payments" }
  if ($p -match 'comms|message|announce|notification') { return "Communications" }
  if ($p -match 'parent') { return "Parent Portal" }
  if ($p -match 'teacher') { return "Teacher Portal" }
  if ($p -match 'admin') { return "Administrator Portal" }
  if ($p -match 'attendance') { return "Attendance" }
  if ($p -match 'schedule|gradebook|section|roster') { return "Scheduling / Gradebook" }
  if ($p -match 'activity|athletic|event') { return "Activities / Events" }
  if ($p -match 'nurse|health') { return "Nurse Office" }
  if ($p -match 'transport') { return "Transportation" }
  if ($p -match 'food|meal|cafeteria') { return "Food Services" }
  if ($p -match 'volunteer|family engagement') { return "Volunteer / Family Engagement" }
  if ($p -match 'board|governance') { return "Board Governance" }
  if ($p -match 'discipline') { return "Extended Discipline" }
  if ($p -match 'spiritual') { return "Spiritual Life" }
  if ($p -match 'outreach|service') { return "Service & Outreach" }
  if ($p -match 'compass') { return "Crown Compass" }
  if ($p -match 'pd[_\- ]?hub|professional development') { return "PD Hub" }
  return "Core / Shared"
}

$repoTop = Get-ChildItem -Force | Select-Object Name, Mode, Length, LastWriteTime | Sort-Object Name; Export-Utf8Csv -Rows $repoTop -Path "$inv\REPO_TOPLEVEL.csv"

$backendApps = @()
if (Test-Path "backend") {
  $backendApps = Get-ChildItem "backend" -Directory | ForEach-Object {
    [pscustomobject]@{
      Name = $_.Name
      FullName = $_.FullName
      Layer = Get-LayerFromPath $_.FullName
      Owner = Get-OwnerFromPath $_.FullName
      CandidateModule = Get-ModuleName $_.FullName
    }
  }
}
Export-Utf8Csv -Rows $backendApps -Path "$inv\BACKEND_APP_INVENTORY.csv"

$frontendDirs = @()
if (Test-Path "frontend") {
  $frontendDirs = Get-ChildItem "frontend" -Directory | ForEach-Object {
    [pscustomobject]@{
      Name = $_.Name
      FullName = $_.FullName
      Layer = Get-LayerFromPath $_.FullName
      Owner = Get-OwnerFromPath $_.FullName
      CandidateModule = Get-ModuleName $_.FullName
    }
  }
}
Export-Utf8Csv -Rows $frontendDirs -Path "$inv\FRONTEND_TOPLEVEL_INVENTORY.csv"

$uiRows = @()
if (Test-Path "frontend") {
  $uiFiles = Get-ChildItem "frontend" -Recurse -File -Include *.jsx,*.tsx,*.js,*.ts -ErrorAction SilentlyContinue
  foreach ($f in $uiFiles) {
    $fp = $f.FullName
    $name = $f.Name.ToLower()
    $dir = $f.DirectoryName.ToLower()
    if ($dir -match '\\pages\\|\\components\\|\\routes\\|\\dashboards\\' -or $name -match 'dashboard|wizard|step\d') {
      $uiKind = if ($name -match 'wizard|step\d') { "Wizard" } elseif ($name -match 'dashboard') { "Dashboard" } else { "PageOrComponent" }
      $uiRows += [pscustomobject]@{
        Path = $fp
        Name = $f.Name
        UIKind = $uiKind
        Layer = Get-LayerFromPath $fp
        CandidateModule = Get-ModuleName $fp
        Owner = "Dev 4"
        KeepRewriteDrop = "MUST_REVIEW"
        RealDataOrPlaceholder = "MUST_REVIEW"
        EndToEndWired = "MUST_REVIEW"
        PermissionsChecked = "MUST_REVIEW"
        TenantSafe = "MUST_REVIEW"
        DuplicateCandidate = "MUST_REVIEW"
        Status = "MUST_REVIEW"
      }
    }
  }
}
$uiRows = $uiRows | Sort-Object Path
Export-Utf8Csv -Rows $uiRows -Path "$inv\DASHBOARD_WIZARD_PAGE_INVENTORY.csv"

$routeRows = @()
if (Test-Path "backend") {
  $apiFiles = Get-ChildItem "backend" -Recurse -File -Include *.py -ErrorAction SilentlyContinue
  foreach ($f in $apiFiles) {
    $content = Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue
    if ($content -match 'urlpatterns|router\.register|api_view\(|ViewSet|APIView|path\(|re_path\(|include\(') {
      $routeRows += [pscustomobject]@{
        Path = $f.FullName
        Name = $f.Name
        Layer = Get-LayerFromPath $f.FullName
        CandidateModule = Get-ModuleName $f.FullName
        Owner = Get-OwnerFromPath $f.FullName
        RouteInventory = "YES"
        AuthChecked = "MUST_REVIEW"
        TenantChecked = "MUST_REVIEW"
        ContractChecked = "MUST_REVIEW"
        DocsChecked = "MUST_REVIEW"
        Status = "MUST_REVIEW"
      }
    }
  }
}
$routeRows = $routeRows | Sort-Object Path
Export-Utf8Csv -Rows $routeRows -Path "$inv\API_ROUTE_CONTRACT_INVENTORY.csv"

$modelServiceRows = @()
if (Test-Path "backend") {
  $msFiles = Get-ChildItem "backend" -Recurse -File -Include *.py -ErrorAction SilentlyContinue
  foreach ($f in $msFiles) {
    $name = $f.Name.ToLower()
    if ($name -match 'models?\.py|services?|serializers?|managers?|signals?|tasks?|commands?') {
      $modelServiceRows += [pscustomobject]@{
        Path = $f.FullName
        Name = $f.Name
        AssetType = Get-AssetType $f.FullName
        Layer = Get-LayerFromPath $f.FullName
        CandidateModule = Get-ModuleName $f.FullName
        Owner = Get-OwnerFromPath $f.FullName
        KeepRewriteDrop = "MUST_REVIEW"
        Status = "MUST_REVIEW"
      }
    }
  }
}
$modelServiceRows = $modelServiceRows | Sort-Object Path
Export-Utf8Csv -Rows $modelServiceRows -Path "$inv\MODEL_SERVICE_INVENTORY.csv"

$testCiDocRows = @()
$allFiles = Get-ChildItem . -Recurse -File -ErrorAction SilentlyContinue
foreach ($f in $allFiles) {
  $path = $f.FullName
  $name = $f.Name.ToLower()
  $dir = $f.DirectoryName.ToLower()
  if (
    $name -match 'test_|_test|spec\.' -or
    $dir -match '\.github\\workflows' -or
    $name -match 'readme|changelog|security|compliance|canon|runbook|guide|report|audit'
  ) {
    $testCiDocRows += [pscustomobject]@{
      Path = $path
      Name = $f.Name
      AssetType = Get-AssetType $path
      Layer = Get-LayerFromPath $path
      CandidateModule = Get-ModuleName $path
      Owner = Get-OwnerFromPath $path
      Status = "MUST_REVIEW"
    }
  }
}
$testCiDocRows = $testCiDocRows | Sort-Object Path
Export-Utf8Csv -Rows $testCiDocRows -Path "$inv\TEST_CI_DOC_INVENTORY.csv"

$masterRows = @()
$allAssetFiles = Get-ChildItem . -Recurse -File -ErrorAction SilentlyContinue
foreach ($f in $allAssetFiles) {
  $masterRows += [pscustomobject]@{
    Path = $f.FullName
    Name = $f.Name
    AssetType = Get-AssetType $f.FullName
    Layer = Get-LayerFromPath $f.FullName
    CandidateModule = Get-ModuleName $f.FullName
    Owner = Get-OwnerFromPath $f.FullName
    KeepRewriteDrop = "MUST_REVIEW"
    InFinalRelease = "MUST_REVIEW"
    Status = "MUST_REVIEW"
  }
}
$masterRows = $masterRows | Sort-Object Path
Export-Utf8Csv -Rows $masterRows -Path "$inv\MASTER_PLATFORM_INVENTORY.csv"

Export-Utf8Csv -Rows ($masterRows | Where-Object { $_.Layer -eq "Core" }) -Path "$inv\CORE_INVENTORY.csv"
Export-Utf8Csv -Rows ($masterRows | Where-Object { $_.Layer -eq "Module" }) -Path "$inv\MODULE_INVENTORY.csv"
Export-Utf8Csv -Rows ($masterRows | Where-Object { $_.Layer -eq "Add-on" }) -Path "$inv\ADDON_INVENTORY.csv"

Write-Host "Inventory complete."
Write-Host "Created:"
Write-Host "  docs\audit\inventories\MASTER_PLATFORM_INVENTORY.csv"
Write-Host "  docs\audit\inventories\DASHBOARD_WIZARD_PAGE_INVENTORY.csv"
Write-Host "  docs\audit\inventories\API_ROUTE_CONTRACT_INVENTORY.csv"

