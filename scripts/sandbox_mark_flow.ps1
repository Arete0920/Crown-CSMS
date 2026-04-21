param(
  [string]$SchoolCode,
  [string]$Role,
  [string]$UserIdentifier = "",
  [string]$LoginPass = "in progress",
  [string]$LandingPass = "in progress",
  [string]$PrimaryFlow = "",
  [string]$PrimaryFlowStatus = "in progress",
  [string]$TenantBoundaryStatus = "in progress",
  [string]$Notes = "",
  [string]$Owner = ""
)
$path = "audit-artifacts/sandbox-launch-5schools/current/02_role_flow_matrix.csv"
$rows = Import-Csv $path
foreach ($r in $rows) {
  if ($r.school_code -eq $SchoolCode -and $r.role -eq $Role) {
    if ($UserIdentifier) { $r.user_identifier = $UserIdentifier }
    $r.login_pass = $LoginPass
    $r.landing_pass = $LandingPass
    if ($PrimaryFlow) { $r.primary_flow = $PrimaryFlow }
    $r.primary_flow_status = $PrimaryFlowStatus
    $r.tenant_boundary_status = $TenantBoundaryStatus
    if ($Notes) { $r.notes = $Notes }
    if ($Owner) { $r.owner = $Owner }
  }
}
$rows | Export-Csv $path -NoTypeInformation -Encoding UTF8
