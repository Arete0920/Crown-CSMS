param(
  [string]$Id,
  [string]$Area,
  [string]$Severity,
  [string]$Blocker,
  [string]$Status = "open",
  [string]$Owner = "",
  [string]$FixCommitOrNote = "",
  [string]$RetestStatus = "not done"
)
$path = "audit-artifacts/sandbox-launch-5schools/current/03_blocker_log.csv"
$row = [pscustomobject]@{
  id = $Id
  opened_at = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
  area = $Area
  severity = $Severity
  blocker = $Blocker
  status = $Status
  owner = $Owner
  fix_commit_or_note = $FixCommitOrNote
  retest_status = $RetestStatus
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
