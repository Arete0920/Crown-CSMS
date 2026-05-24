$base = "c:\Users\JMega\OneDrive\Desktop\Crown2026\frontend\dashboards\src\pages"
$dashboards = @(
  "AdminDashboard","AdvancementDashboard","FacilitiesDashboard","HealthDashboard",
  "HumanResources","ITDashboard","AthleticsDashboard","FoodDashboard",
  "SpiritualLifeDashboard","CounselingDashboard","LibraryDashboard","MarketingDashboard",
  "SafetyDashboard","TransportationDashboard","ParentDashboard","StudentDashboard",
  "ExtendedCareDashboard","RegistrarDashboard","PDDashboard","AcademicSupportDashboard",
  "FineArtsDashboard","CommunicationsDirectorDashboard","SecurityDashboard","OfficeDashboard",
  "FinancialAidDashboard","BillingDashboard","TeacherDashboard","IntegrityDashboard",
  "BoardDashboard","BoardExecutiveDashboard"
)
$importSingle = "import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';"
$importDouble = 'import { KpiStrip } from "../components/dashboard/KpiFlipCard.jsx";'
$count = 0
foreach ($d in $dashboards) {
  $path = "$base\$d.jsx"
  if (!(Test-Path $path)) { Write-Host "MISSING: $d"; continue }
  $content = Get-Content $path -Raw -Encoding UTF8
  if ($content -match "KpiFlipCard") { Write-Host "SKIP: $d"; continue }
  $lines = $content -split "`n"
  $lastIdx = -1
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match "^import ") { $lastIdx = $i }
  }
  if ($lastIdx -ge 0) {
    $useDouble = ($lines[0..$lastIdx] | Where-Object {$_ -match '^import.*"\.\./'}) -ne $null
    $imp = if ($useDouble) { $importDouble } else { $importSingle }
    $before = $lines[0..$lastIdx]
    $after  = if ($lastIdx+1 -lt $lines.Count) { $lines[($lastIdx+1)..($lines.Count-1)] } else { @() }
    $newLines = $before + $imp + $after
    [System.IO.File]::WriteAllText($path, ($newLines -join "`n"), [System.Text.Encoding]::UTF8)
    Write-Host "ADDED: $d"
    $count++
  } else {
    Write-Host "NO IMPORT FOUND: $d"
  }
}
Write-Host "Done: $count files updated"
