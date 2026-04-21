param(
  [string]$SchoolCode,
  [string]$BaseUrl = "",
  [string]$Admin = "",
  [string]$Parent = "",
  [string]$Teacher = "",
  [string]$Finance = "",
  [string]$Admissions = "",
  [string]$LoginStatus = "in progress",
  [string]$LandingStatus = "in progress",
  [string]$Notes = "",
  [string]$Owner = ""
)
$path = "audit-artifacts/sandbox-launch-5schools/current/01_school_matrix.csv"
$rows = Import-Csv $path
foreach ($r in $rows) {
  if ($r.school_code -eq $SchoolCode) {
    if ($BaseUrl) { $r.base_url = $BaseUrl }
    if ($Admin) { $r.admin_account = $Admin }
    if ($Parent) { $r.parent_account = $Parent }
    if ($Teacher) { $r.teacher_account = $Teacher }
    if ($Finance) { $r.finance_account = $Finance }
    if ($Admissions) { $r.admissions_account = $Admissions }
    $r.login_status = $LoginStatus
    $r.landing_status = $LandingStatus
    if ($Notes) { $r.notes = $Notes }
    if ($Owner) { $r.owner = $Owner }
  }
}
$rows | Export-Csv $path -NoTypeInformation -Encoding UTF8
