# Crown Operations Alert Runbook

## SLA Thresholds, Escalation Path, and Incident Response

Owner: Crown DevOps / Engineering Lead

## Production SLA Targets

| Metric | Target | Alert Threshold | P0 Threshold |
|---|---|---|---|
| Uptime | 99.5% monthly | < 99.9% in 24h | < 99% in 1h |
| API p95 response (reads) | < 500ms | > 750ms for 5 min | > 2000ms for 5 min |
| API p95 response (writes) | < 2000ms | > 3000ms for 5 min | > 5000ms for 5 min |
| Health endpoint p99 | < 200ms | > 500ms | > 1000ms |
| Error rate | < 0.1% | > 0.5% over 5 min | > 1% over 2 min |
| Authentication failure rate | < 1% | > 5% over 5 min | > 10% over 2 min |
| Deploy success rate | 100% | Any failed deploy | Two consecutive failures |

## Alert Routing

| Severity | Response SLA | Who Gets Paged | Channel |
|---|---|---|---|
| P0 - Production down | 15 minutes | TC plus engineering lead | Phone and Slack |
| P1 - Degraded performance | 1 hour | Engineering lead | Slack |
| P2 - Non-critical error spike | 4 hours | On-call engineer | Slack |
| P3 - Warning threshold | Next business day | Engineering team | Monitoring channel |

## Runbook: Production Health Check Failure

1. Call `/api/health/` directly and inspect the JSON payload.
2. Review Sentry for the last 15 minutes.
3. Check Azure App Service health and restart status.
4. Review the most recent deployment workflow.
5. If the database is unhealthy, inspect the database service.

## Runbook: Authentication Failures Spike

1. Check Sentry for authentication errors.
2. Verify token secrets and auth configuration.
3. Verify Microsoft identity dependencies if applicable.
4. Escalate if root cause is not identified within 30 minutes.

## Runbook: Deploy Failure

1. Stop additional merges to `main` until the pipeline is green.
2. Inspect the failed workflow step.
3. Reproduce locally.
4. Fix the root cause rather than bypassing the gate.

## Runbook: Data Incident / Suspected FERPA Breach

1. Contain access immediately.
2. Pull audit evidence and assess scope.
3. Notify the compliance owner.
4. Notify affected schools within policy timelines.
5. Preserve logs and evidence.