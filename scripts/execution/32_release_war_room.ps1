$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$base = Join-Path $repoRoot "audit-artifacts\release-war-room"
New-Item -ItemType Directory -Force -Path $base | Out-Null

$priorityPath = Join-Path $base "priority_board.csv"
$checklistPath = Join-Path $base "cutover_rollback_checklist.md"

if (-not (Test-Path $priorityPath)) {
    @"
Priority,Area,Owner,Status,ExitCriteria,ArtifactOrFile,Notes
1,Django check,Dev 1,Open,"python backend\manage.py check passes","audit-artifacts\runtime-release-closure\latest\03_django_check.txt",
2,Showmigrations,Dev 2,Open,"python backend\manage.py showmigrations is clean","audit-artifacts\runtime-release-closure\latest\04_showmigrations.txt",
3,Deploy check,Dev 1,Open,"python backend\manage.py check --deploy passes","audit-artifacts\runtime-release-closure\latest\05_deploy_check.txt",
4,Health endpoint,Dev 5,Open,"GET /api/health/ returns success","audit-artifacts\runtime-release-closure\latest\06_health_endpoint.txt",
5,Integrity endpoint,Dev 5,Open,"GET /api/integrity/ returns success","audit-artifacts\runtime-release-closure\latest\07_integrity_endpoint.txt",
6,Release evidence rerun,Dev 5,Open,"Full runtime closure rerun is clean","audit-artifacts\runtime-release-closure\latest\SUMMARY.md",
7,Payment readiness,Joanne,Open,"All checklist items complete and signed","audit-artifacts\post-merge-closeout\20260418_064158\04_launch_trackers\01_payment_validation_checklist.md",
8,Legal DPA readiness,TC,Open,"School-facing legal packet ready","audit-artifacts\post-merge-closeout\20260418_064158\04_launch_trackers\02_legal_dpa_readiness.md",
9,Pilot / LOI conversion,TC,Open,"At least one signed LOI and scheduled pilot","audit-artifacts\post-merge-closeout\20260418_064158\04_launch_trackers\03_pilot_loi_tracker.md",
10,Cutover and rollback rehearsal,Dev 5,Open,"Dry run and rollback proof complete","audit-artifacts\release-war-room\cutover_rollback_checklist.md",
"@ | Set-Content $priorityPath -Encoding utf8
}

if (-not (Test-Path $checklistPath)) {
    @"
# Cutover and Rollback Checklist

## Owners
- Release:
- Rollback:
- Verification:
- Final sign-off:

## Cutover
- [ ] deployment command documented
- [ ] env vars verified
- [ ] database backup verified
- [ ] migration plan verified
- [ ] smoke test list ready

## Rollback
- [ ] rollback command documented
- [ ] prior artifact available
- [ ] database rollback path documented
- [ ] verification steps documented

## Final proof
- [ ] cutover rehearsal completed
- [ ] rollback rehearsal completed
- [ ] timestamps captured
- [ ] go/no-go signed
"@ | Set-Content $checklistPath -Encoding utf8
}

Write-Host "Done: $base"
