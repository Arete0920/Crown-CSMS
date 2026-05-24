[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [string]$Repo,

  [Parameter(Mandatory=$true)]
  [string]$Tag,

  [Parameter(Mandatory=$true)]
  [string]$ExpectedSha,

  [Parameter(Mandatory=$true)]
  [string]$HealthUrl,

  [Parameter(Mandatory=$false)]
  [string]$WorkflowName = "Production Deploy",

  [Parameter(Mandatory=$false)]
  [int]$TimeoutSec = 25
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Require-Cmd($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "Missing required command: $name"
  }
}

function Normalize-Sha([string]$s) {
  if (-not $s) { return "" }
  return $s.Trim().ToLowerInvariant()
}

function Print-Header([string]$title) {
  Write-Host ""
  Write-Host ("=" * 80)
  Write-Host $title
  Write-Host ("=" * 80)
}

Require-Cmd "gh"

$env:GH_PAGER = "cat"
$env:GH_FORCE_TTY = "0"

$expected = Normalize-Sha $ExpectedSha

Print-Header "1) TAG -> SHA proof"
$tagObjSha = Normalize-Sha (gh api "/repos/$Repo/git/ref/tags/$Tag" --jq ".object.sha" 2>$null)
$tagObjType = gh api "/repos/$Repo/git/ref/tags/$Tag" --jq ".object.type" 2>$null
if (-not $tagObjSha) { throw "Tag not found in repo: $Repo tag=$Tag" }

$tagCommitSha = $tagObjSha
if ($tagObjType -eq "tag") {
  $tagCommitSha = Normalize-Sha (gh api "/repos/$Repo/git/tags/$tagObjSha" --jq ".object.sha")
  $tagObjType = gh api "/repos/$Repo/git/tags/$tagObjSha" --jq ".object.type"
}

Write-Host "Repo:        $Repo"
Write-Host "Tag:         $Tag"
Write-Host "Tag type:    $tagObjType"
Write-Host "Tag commit:  $tagCommitSha"
Write-Host "Expected:    $expected"

if ($tagCommitSha -ne $expected) {
  throw "FAIL: Tag $Tag does not point to ExpectedSha. tagCommit=$tagCommitSha expected=$expected"
}
Write-Host "PASS: Tag points to ExpectedSha."

Print-Header "2) PROD /api/health -> build_sha proof"
try {
  $health = Invoke-RestMethod -Uri $HealthUrl -Method GET -TimeoutSec $TimeoutSec
} catch {
  throw "FAIL: Health endpoint unreachable: $HealthUrl :: $($_.Exception.Message)"
}

$buildSha = ""
if ($health.PSObject.Properties.Name -contains "build_sha") { $buildSha = $health.build_sha }
elseif ($health.PSObject.Properties.Name -contains "BUILD_SHA") { $buildSha = $health.BUILD_SHA }

$envName = ""
if ($health.PSObject.Properties.Name -contains "env") { $envName = $health.env }
elseif ($health.PSObject.Properties.Name -contains "environment") { $envName = $health.environment }

$dbStatus = ""
if ($health.PSObject.Properties.Name -contains "db") { $dbStatus = $health.db }

$buildShaNorm = Normalize-Sha $buildSha

Write-Host "HealthUrl:   $HealthUrl"
Write-Host "env:         $envName"
Write-Host "db:          $dbStatus"
Write-Host "build_sha:   $buildShaNorm"
Write-Host "expected:    $expected"

if (-not $buildShaNorm) {
  throw "FAIL: Health JSON missing build_sha (or BUILD_SHA). Raw keys: $($health.PSObject.Properties.Name -join ', ')"
}
if ($buildShaNorm -ne $expected) {
  throw "FAIL: Prod build_sha mismatch. prod=$buildShaNorm expected=$expected"
}
Write-Host "PASS: Prod health build_sha matches ExpectedSha."

Print-Header "3) Latest Production Deploy run (optional evidence)"
 $runId = gh run list --repo $Repo --workflow $WorkflowName --limit 1 --json databaseId --jq ".[]?.databaseId"
if ($runId) {
  $runStatus = gh run list --repo $Repo --workflow $WorkflowName --limit 1 --json status --jq ".[]?.status"
  $runConclusion = gh run list --repo $Repo --workflow $WorkflowName --limit 1 --json conclusion --jq ".[]?.conclusion"
  $runHeadSha = Normalize-Sha (gh run list --repo $Repo --workflow $WorkflowName --limit 1 --json headSha --jq ".[]?.headSha")
  $runEvent = gh run list --repo $Repo --workflow $WorkflowName --limit 1 --json event --jq ".[]?.event"
  $runUrl = gh run list --repo $Repo --workflow $WorkflowName --limit 1 --json url --jq ".[]?.url"

  Write-Host ("run_id:      {0}" -f $runId)
  Write-Host ("status:      {0}" -f $runStatus)
  Write-Host ("conclusion:  {0}" -f $runConclusion)
  Write-Host ("headSha:     {0}" -f $runHeadSha)
  Write-Host ("event:       {0}" -f $runEvent)
  Write-Host ("url:         {0}" -f $runUrl)

  if ($runStatus -ne "completed" -or $runConclusion -ne "success") {
    throw "FAIL: Latest '$WorkflowName' run is not successful."
  }
  Write-Host "PASS: Latest '$WorkflowName' run is successful (evidence)."
} else {
  Write-Host "WARN: Could not fetch latest '$WorkflowName' run."
}

Print-Header "FINAL RESULT"
Write-Host "PASS: Production integrity proof succeeded (Tag -> SHA -> Prod Health)."