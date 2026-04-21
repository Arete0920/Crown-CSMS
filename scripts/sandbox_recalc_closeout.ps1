$cur = "audit-artifacts/sandbox-launch-5schools/current"
$schools = Import-Csv "$cur/01_school_matrix.csv"
$flows = Import-Csv "$cur/02_role_flow_matrix.csv"
$blockers = Import-Csv "$cur/03_blocker_log.csv"
$risks = Import-Csv "$cur/04_risk_register.csv"
$loginsDone = ($schools | Where-Object { $_.login_status -eq "completed and verified" -and $_.landing_status -eq "completed and verified" }).Count
$flowsDone = ($flows | Where-Object { $_.login_pass -eq "completed and verified" -and $_.landing_pass -eq "completed and verified" -and $_.primary_flow_status -eq "completed and verified" }).Count
$tenantDone = ($flows | Where-Object { $_.tenant_boundary_status -eq "completed and verified" }).Count
$openBlockers = ($blockers | Where-Object { $_.id -and $_.status -ne "closed" -and $_.status -ne "completed and verified" }).Count
$openRisks = ($risks | Where-Object { $_.id -and $_.status -ne "closed" -and $_.status -ne "completed and verified" }).Count
$matrixStatus = "in progress"
$flowStatus = "in progress"
$tenantStatus = "in progress"
$recommendation = "not ready"
if ($loginsDone -ge 5) { $matrixStatus = "completed and verified" }
if ($flowsDone -ge 25) { $flowStatus = "completed and verified" }
if ($tenantDone -ge 25) { $tenantStatus = "completed and verified" }
if ($loginsDone -ge 5 -and $flowsDone -ge 25 -and $tenantDone -ge 25 -and $openBlockers -eq 0) {
  $recommendation = "ready"
} elseif ($loginsDone -ge 5 -and $flowsDone -ge 15) {
  $recommendation = "ready with minor known issues"
}
@"
# Final Go / No-Go

Runtime health:
- completed and verified

Runtime integrity:
- completed and verified

5-school login matrix:
- $matrixStatus

Role-flow proof:
- $flowStatus

Tenant proof:
- $tenantStatus

Blocker count:
- $openBlockers

Residual risks:
- $openRisks

Tomorrow-morning recommendation:
- $recommendation
"@ | Set-Content "$cur/20_final_go_no_go.md" -Encoding UTF8
Get-Content "$cur/20_final_go_no_go.md"
