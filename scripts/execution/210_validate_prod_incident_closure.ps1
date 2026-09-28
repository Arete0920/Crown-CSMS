param(
	[string]$Repo = "Arete0920/Crown-CSMS",
	[string]$ProdHealthUrl = "https://crown-api-prod.azurewebsites.net/api/health/",
	[int[]]$IncidentIssues = @(795,796,797,798),
	[string]$OutDir = "audit-artifacts/production-incident-closure"
)

$ErrorActionPreference = "Stop"

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$RunDir = Join-Path $OutDir $Stamp
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Write-JsonFile($Path, $Object) {
	$Object | ConvertTo-Json -Depth 30 | Out-File -FilePath $Path -Encoding UTF8
}

function Stop-Fail($Message) {
	$Result = [ordered]@{
		generated_at = (Get-Date).ToString("s")
		gate = "FAIL"
		reason = $Message
	}
	Write-JsonFile (Join-Path $RunDir "gate_result.json") $Result
	Write-Host "FAIL: $Message" -ForegroundColor Red
	exit 1
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
	Stop-Fail "GitHub CLI gh is not installed."
}

try {
	$HealthResponse = Invoke-WebRequest -Uri $ProdHealthUrl -UseBasicParsing -TimeoutSec 30
} catch {
	Stop-Fail "Production health request failed: $($_.Exception.Message)"
}

$HealthRawPath = Join-Path $RunDir "prod_health_raw.json"
$HealthResponse.Content | Out-File -FilePath $HealthRawPath -Encoding UTF8

if ($HealthResponse.StatusCode -ne 200) {
	Stop-Fail "Production health returned HTTP $($HealthResponse.StatusCode), expected 200."
}

$Health = $HealthResponse.Content | ConvertFrom-Json

$HealthOk =
	(($Health.ok -eq $true) -or ($Health.status -eq "ok")) -and
	($Health.db -eq "ok") -and
	($Health.env -eq "prod")

if (-not $HealthOk) {
	Stop-Fail "Production health payload is not clean. Required env=prod, db=ok, ok=true or status=ok."
}

$Issues = @()
foreach ($IssueNumber in $IncidentIssues) {
	$Raw = gh issue view $IssueNumber --repo $Repo --json number,title,state,labels,createdAt,updatedAt,url,body 2>&1
	if ($LASTEXITCODE -ne 0) {
		Stop-Fail "Could not read issue #$IssueNumber. $Raw"
	}
	$Issues += ($Raw | ConvertFrom-Json)
}

Write-JsonFile (Join-Path $RunDir "incident_issues.json") $Issues

$OpenIncidents = @($Issues | Where-Object { $_.state -eq "OPEN" })
$ClosedIncidents = @($Issues | Where-Object { $_.state -eq "CLOSED" })

$RecentRunsRaw = gh run list --repo $Repo --limit 30 --json databaseId,name,workflowName,status,conclusion,event,headSha,createdAt,updatedAt,url 2>&1
if ($LASTEXITCODE -ne 0) {
	Stop-Fail "Could not read GitHub Actions runs. $RecentRunsRaw"
}
$RecentRuns = $RecentRunsRaw | ConvertFrom-Json
Write-JsonFile (Join-Path $RunDir "recent_workflow_runs.json") $RecentRuns

$ReleaseEvidencePrsRaw = gh pr list --repo $Repo --state open --search "release evidence OR release lineage OR final release gate closure" --json number,title,state,isDraft,mergeable,url,headRefName,baseRefName,updatedAt 2>&1
if ($LASTEXITCODE -eq 0) {
	$ReleaseEvidencePrs = $ReleaseEvidencePrsRaw | ConvertFrom-Json
} else {
	$ReleaseEvidencePrs = @()
}
Write-JsonFile (Join-Path $RunDir "open_release_evidence_prs.json") $ReleaseEvidencePrs

$DjangoPrsRaw = gh pr list --repo $Repo --state open --search "django 5.2.14" --json number,title,state,isDraft,mergeable,url,headRefName,baseRefName,updatedAt 2>&1
if ($LASTEXITCODE -eq 0) {
	$DjangoPrs = $DjangoPrsRaw | ConvertFrom-Json
} else {
	$DjangoPrs = @()
}
Write-JsonFile (Join-Path $RunDir "open_django_security_prs.json") $DjangoPrs

$Score = [ordered]@{
	generated_at = (Get-Date).ToString("s")
	repo = $Repo
	prod_health_url = $ProdHealthUrl
	prod_health_http = $HealthResponse.StatusCode
	prod_env = $Health.env
	prod_status = $Health.status
	prod_ok = $Health.ok
	prod_db = $Health.db
	prod_version = $Health.version
	prod_build_sha = $Health.build_sha
	prod_deploy_tag = $Health.deploy_tag
	prod_deploy_run_id = $Health.deploy_run_id
	prod_deploy_workflow = $Health.deploy_workflow
	target_incidents_total = $IncidentIssues.Count
	target_incidents_open = $OpenIncidents.Count
	target_incidents_closed = $ClosedIncidents.Count
	open_release_evidence_prs = @($ReleaseEvidencePrs).Count
	open_django_security_prs = @($DjangoPrs).Count
	runtime_health_gate = "PASS"
	incident_backlog_gate = $(if ($OpenIncidents.Count -eq 0) { "PASS" } else { "FAIL" })
	release_evidence_gate = $(if (@($ReleaseEvidencePrs).Count -eq 0) { "PASS" } else { "FAIL" })
	django_security_gate = $(if (@($DjangoPrs).Count -eq 0) { "PASS" } else { "FAIL" })
	final_release_gate = "NO-GO"
}

if (
	$Score.runtime_health_gate -eq "PASS" -and
	$Score.incident_backlog_gate -eq "PASS" -and
	$Score.release_evidence_gate -eq "PASS" -and
	$Score.django_security_gate -eq "PASS"
) {
	$Score.final_release_gate = "CONDITIONALLY CLEAN FROM THIS SCRIPT ONLY"
}

Write-JsonFile (Join-Path $RunDir "live_scorecard.json") $Score

$Md = @()
$Md += "# CROWN Live Production Incident Closure Scorecard"
$Md += ""
$Md += "Generated: $($Score.generated_at)"
$Md += ""
$Md += "| Gate | Result |"
$Md += "|---|---|"
$Md += "| Runtime health | $($Score.runtime_health_gate) |"
$Md += "| Target incident backlog | $($Score.incident_backlog_gate) |"
$Md += "| Release evidence PRs | $($Score.release_evidence_gate) |"
$Md += "| Django security PRs | $($Score.django_security_gate) |"
$Md += "| Final release gate | $($Score.final_release_gate) |"
$Md += ""
$Md += "## Production Health"
$Md += ""
$Md += "| Field | Value |"
$Md += "|---|---|"
$Md += "| HTTP | $($Score.prod_health_http) |"
$Md += "| env | $($Score.prod_env) |"
$Md += "| status | $($Score.prod_status) |"
$Md += "| ok | $($Score.prod_ok) |"
$Md += "| db | $($Score.prod_db) |"
$Md += "| version | $($Score.prod_version) |"
$Md += "| build_sha | $($Score.prod_build_sha) |"
$Md += "| deploy_tag | $($Score.prod_deploy_tag) |"
$Md += "| deploy_run_id | $($Score.prod_deploy_run_id) |"
$Md += "| deploy_workflow | $($Score.prod_deploy_workflow) |"
$Md += ""
$Md += "## Target Incidents"
$Md += ""
foreach ($Issue in $Issues) {
	$Md += "- #$($Issue.number): $($Issue.state) â€” $($Issue.title)"
}
$Md += ""
$Md += "## Open Release Evidence PRs"
$Md += ""
if (@($ReleaseEvidencePrs).Count -eq 0) {
	$Md += "- None"
} else {
	foreach ($Pr in $ReleaseEvidencePrs) {
		$Md += "- #$($Pr.number): $($Pr.title) â€” $($Pr.url)"
	}
}
$Md += ""
$Md += "## Open Django Security PRs"
$Md += ""
if (@($DjangoPrs).Count -eq 0) {
	$Md += "- None"
} else {
	foreach ($Pr in $DjangoPrs) {
		$Md += "- #$($Pr.number): $($Pr.title) â€” $($Pr.url)"
	}
}

$Md -join "`n" | Out-File -FilePath (Join-Path $RunDir "live_scorecard.md") -Encoding UTF8

Write-Host ""
Write-Host "Runtime health:        $($Score.runtime_health_gate)"
Write-Host "Incident backlog:      $($Score.incident_backlog_gate)"
Write-Host "Release evidence PRs:  $($Score.release_evidence_gate)"
Write-Host "Django security PRs:   $($Score.django_security_gate)"
Write-Host "Final release gate:    $($Score.final_release_gate)"
Write-Host ""
Write-Host "Artifacts: $RunDir"
