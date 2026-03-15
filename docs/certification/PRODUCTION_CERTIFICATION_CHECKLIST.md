# Crown2026 Production Certification Checklist

Status date: 2026-03-15
Certification state: Not certified

This checklist is separate from branch stabilization and module completion.
Production certification requires all items marked Pass with evidence.

## Release tuple (must match exactly)

- Candidate branch:
- Candidate head sha:
- RC artifact sha:
- RC tag:
- Deploy workflow run URL:
- Deployed sha:
- Runtime build_sha:
- Runtime prod_deploy_tag:

## Checklist

### 1) Deployment truth
- [ ] Deploy workflow completed successfully
- [ ] Deployed sha equals candidate head sha
- [ ] Runtime health status is ok
- [ ] Runtime build_sha equals deployed sha
- [ ] Runtime prod_deploy_tag equals release tag

### 2) Environment truth
- [ ] Environment mode verified (prod)
- [ ] Debug disabled
- [ ] Demo mode disabled in production
- [ ] Required app settings present and non-placeholder

### 3) Rollback readiness
- [ ] Last known good release identified
- [ ] Rollback command and owner documented
- [ ] Rollback tested in non-prod or rehearsal evidence provided

### 4) Monitoring and alerting
- [ ] Health endpoint monitored
- [ ] Error budget or alert thresholds documented
- [ ] On-call or escalation path documented

### 5) Security and compliance
- [ ] Secret scan clean for release sha
- [ ] Code scanning checks green for release sha
- [ ] Tenant enforcement checks pass for release sha
- [ ] Branch protection and required checks intact

### 6) Supportability and operations
- [ ] Logs accessible and queryable
- [ ] Backup and restore posture documented
- [ ] Incident response runbook linked
- [ ] Owner handoff contact list current

### 7) Functional release gates
- [ ] Bucket 1 blockers closed for release sha
- [ ] Required proof jobs green for release sha
- [ ] Required smoke tests green for release sha
- [ ] Module acceptance signoffs updated

## Certification signoff

- Certification lead:
- Date and time UTC:
- Evidence folder path:
- Final decision: Pass or Fail
- Notes:
