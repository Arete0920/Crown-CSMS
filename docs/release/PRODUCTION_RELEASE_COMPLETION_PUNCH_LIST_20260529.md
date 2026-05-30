# Production Release Completion Punch List - 2026-05-29

## P0 - Required Before Broad Production Claim
- [ ] latest main Release Verify green
- [ ] latest main contract-gate green
- [ ] live Azure health smoke green
- [ ] role-route smoke for parent/teacher/admin/finance/admissions
- [ ] billing golden path green
- [ ] admissions golden path green
- [ ] frontend truth disclosure verified in deployed UI
- [ ] release scope lock published

## P1 - Scheduling Completion
- [ ] update scheduling branch from latest main
- [ ] run Django check
- [ ] run makemigrations dry-run
- [ ] run migrate plan
- [ ] run scheduling tests
- [ ] run academics + scheduling tests
- [ ] complete admin dashboard Scheduling pages
- [ ] complete schedule setup wizard
- [ ] complete bell schedule builder UI
- [ ] complete section meeting editor
- [ ] complete conflict report table
- [ ] complete publish flow
- [ ] complete student/parent/teacher schedule views
- [ ] hosted gates green before merge

## P2 - Persona and Dashboard Completion Audit
- [ ] inventory all personas
- [ ] map each persona to dashboard route
- [ ] verify authorization
- [ ] verify live/demo/unavailable disclosure
- [ ] verify no dead navigation
- [ ] verify backend route support
- [ ] verify frontend truth disclosure
- [ ] verify role-route behavior

Personas to explicitly verify:
- [ ] parent
- [ ] student
- [ ] teacher
- [ ] coach
- [ ] administrator
- [ ] board
- [ ] finance
- [ ] admissions

Verification dimensions:
- [ ] permissions
- [ ] routes
- [ ] dashboards
- [ ] navigation
- [ ] truth disclosure

## P3 - SOLOMON Controlled Growth
- [ ] keep source corpus manual
- [ ] no ingestion until provenance model approved
- [ ] publisher metadata only
- [ ] BJU POC index only
- [ ] no AI activation
- [ ] no student-facing search
- [ ] no Teams/SharePoint sync
- [ ] corpus acquisition planning completed
- [ ] provenance implementation plan completed
- [ ] attribution implementation plan completed
- [ ] canonical/advisory governance plan completed
- [ ] publisher metadata framework documented

## P4 - Hygiene
- [ ] preserve worktree discipline
- [ ] no broad Autopilot edits
- [ ] explicit-path commits only
- [ ] stale branches reviewed
- [ ] release docs updated after every gate

Publisher strategy controls:
- [ ] BJU metadata-only pilot
- [ ] publisher outreach plan
- [ ] rights framework documented
- [ ] partnership program criteria defined
