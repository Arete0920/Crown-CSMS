# Production Deploy Rapid Triage Matrix

| Failed Step | Likely Cause | Immediate Check | Fast Action |
|---|---|---|---|
| Guard: Azure auth secrets present | Missing/invalid secrets | Workflow guard output | Correct secret values and rerun |
| Guard: OIDC federation diagnostics / Azure Login (OIDC) | Federated credential mismatch | Compare logged subject + audience with Azure credential | Update federated credential subject/audience |
| Verify AcrPull Identity (Guardrail) | Managed identity lacks AcrPull or transient Azure read | Principal ID, ACR ID, role assignment query | Grant AcrPull and rerun |
| Build and push Docker image | Registry auth/build issue | Build logs + ACR login step | Fix registry auth/build context |
| Run security scan (Trivy) | Scan or image pull issue | Image tag pull + scan output | Retry after pull validation |
| Upload coverage | Missing coverage.xml | Coverage artifact status step | Ensure coverage generated before upload |
| Verify deployed build SHA and tenant-aware integrity | Wrong build deployed, appsettings mismatch, tenant probe failure | Health/integrity payload and expected SHA | Re-apply appsettings/restart, verify tenant ID |

## Supporting Reports
- `docs/audit/reports/FINAL_EXECUTIVE_AUDIT_SUMMARY.md`
- `docs/audit/reports/FINAL_AUDIT_SCORECARD.md`
- `docs/audit/reports/EXEC_BOARD_REPORT.md`
- `docs/audit/reports/BOARD_TOP_25_BLOCKERS.csv`
