`$ErrorActionPreference = "Stop"

`$Repo = "$Repo"
`$IncidentIssues = @($($IncidentIssues -join ","))
`$ProdHealthUrl = "$ProdHealthUrl"

try {
	`$HealthResponse = Invoke-WebRequest -Uri `$ProdHealthUrl -UseBasicParsing -TimeoutSec 30
} catch {
	throw "Production health check failed before closure: `$(`$_.Exception.Message)"
}

if (`$HealthResponse.StatusCode -ne 200) {
	throw "Production health returned non-200 before closure: `$(`$HealthResponse.StatusCode)"
}

`$HealthJson = `$HealthResponse.Content | ConvertFrom-Json

`$HealthOk =
	((`$HealthJson.ok -eq `$true) -or (`$HealthJson.status -eq "ok")) -and
	(`$HealthJson.db -eq "ok") -and
	(`$HealthJson.env -eq "prod")

if (-not `$HealthOk) {
	throw "Production health payload is not clean before closure."
}

`$ClosureComment = @"
Validated production runtime recovery before incident closure.

Health endpoint: `$ProdHealthUrl

Current health:
- HTTP: `$(`$HealthResponse.StatusCode)
- env: `$(`$HealthJson.env)
- status: `$(`$HealthJson.status)
- ok: `$(`$HealthJson.ok)
- db: `$(`$HealthJson.db)
- version: `$(`$HealthJson.version)
- build_sha: `$(`$HealthJson.build_sha)
- deploy_tag: `$(`$HealthJson.deploy_tag)
- deploy_run_id: `$(`$HealthJson.deploy_run_id)
- deploy_workflow: `$(`$HealthJson.deploy_workflow)

Closure meaning:
- This closes the incident record because production runtime is currently healthy.
- This does not assert GA readiness.
- This does not assert deployment pipeline perfection.
- Release readiness remains gated by merged evidence, required checks, security updates, and branch/ruleset proof.
"@

foreach (`$IssueNumber in `$IncidentIssues) {
	`$IssueJson = gh issue view `$IssueNumber --repo `$Repo --json state,title,labels | ConvertFrom-Json
	if (`$IssueJson.state -ne "OPEN") {
		Write-Host "SKIP #`$IssueNumber already closed"
		continue
	}

	gh issue comment `$IssueNumber --repo `$Repo --body `$ClosureComment
	if (`$LASTEXITCODE -ne 0) { throw "Failed to comment on issue #`$IssueNumber" }

	gh issue close `$IssueNumber --repo `$Repo --reason completed
	if (`$LASTEXITCODE -ne 0) { throw "Failed to close issue #`$IssueNumber" }

	Write-Host "CLOSED #`$IssueNumber"
}
