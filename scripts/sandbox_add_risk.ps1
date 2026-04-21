param(
  [string]$Id,
  [string]$Risk,
  [string]$Severity = "",
  [string]$Probability = "",
  [string]$Mitigation = "",
  [string]$Owner = "",
  [string]$NextReview = "",
  [string]$Status = "open"
)
$path = "audit-artifacts/sandbox-launch-5schools/current/04_risk_register.csv"
$row = [pscustomobject]@{
  id = $Id
  opened_at = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
  risk = $Risk
  severity = $Severity
  probability = $Probability
  mitigation = $Mitigation
  owner = $Owner
  next_review = $NextReview
  status = $Status
}

$rows = @()
if (Test-Path $path) {
  $imported = Import-Csv $path
  if ($imported -is [System.Array]) {
    $rows = $imported
  } elseif ($imported) {
    $rows = @($imported)
  }
}
$rows = $rows + @($row)
$rows | Export-Csv $path -NoTypeInformation -Encoding UTF8
