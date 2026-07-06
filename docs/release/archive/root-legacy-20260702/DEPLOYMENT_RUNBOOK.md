# DEPLOYMENT_RUNBOOK.md
**Pre-Deployment Checks:**
- [ ] Obtain authority signature (FINAL_AUTHORITY_SIGNOFF.md)
- [ ] Confirm production health endpoint is live
- [ ] Run final gate on production baseline
- [ ] Verify all backlog PRs are merged
- [ ] Backup production database

**Deployment Steps:**
1. Tag release: git tag -a release/2026-05-18-final
2. Push tag: git push origin release/2026-05-18-final
3. Deploy to staging: Verify health metrics
4. Deploy to production: Monitor error rates
5. Validate build_sha: Compare production vs. baseline

**Rollback Plan:**
- Revert to previous tag if critical issues detected
- Maintain previous version in standby
- Schedule post-incident review

