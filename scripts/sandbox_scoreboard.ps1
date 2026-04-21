param(
  [string]$Checkpoint,
  [string]$RuntimeHealth = "in progress",
  [string]$RuntimeIntegrity = "in progress",
  [string]$SchoolMatrix = "in progress",
  [string]$RoleFlows = "in progress",
  [string]$TenantProof = "in progress",
  [string]$FrontendLint = "in progress",
  [string]$FrontendBuild = "in progress",
  [string]$Notes = "",
  [string]$Status = "in progress"
)
$path = "audit-artifacts/sandbox-launch-5schools/current/05_hourly_scoreboard.csv"
$rows = Import-Csv $path
foreach ($r in $rows) {
  if ($r.checkpoint -eq $Checkpoint) {
    $r.runtime_health = $RuntimeHealth
    $r.runtime_integrity = $RuntimeIntegrity
    $r.school_matrix = $SchoolMatrix
    $r.role_flows = $RoleFlows
    $r.tenant_proof = $TenantProof
    $r.frontend_lint = $FrontendLint
    $r.frontend_build = $FrontendBuild
    $r.notes = $Notes
    $r.status = $Status
  }
}
$rows | Export-Csv $path -NoTypeInformation -Encoding UTF8
