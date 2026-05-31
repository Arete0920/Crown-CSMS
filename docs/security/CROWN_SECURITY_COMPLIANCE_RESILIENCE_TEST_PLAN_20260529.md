# CROWN Security, Compliance, and Resilience Test Plan — 2026-05-29

## Decision

**Automated compliance and vulnerability scanning: APPROVED FOR NON-DESTRUCTIVE CI USE.**

**Chaos engineering / fault injection: BLOCKED UNTIL CHAOS-READINESS GATE IS GREEN.**

This plan separates safe scanning from destructive resilience testing. CROWN may run non-destructive repository, dependency, static, and compliance checks now. CROWN must not run disruptive chaos experiments against production, pilot, or any environment containing real school data until all safety prerequisites are proven.

## Phase 1 — Safe now: automated compliance and vulnerability scanning

Approved for CI and local execution:

| Control | Purpose | Destructive? | Current decision |
|---|---|---:|---|
| Secret scanning | Detect committed secrets, tokens, passwords, private keys | No | APPROVED |
| Dependency vulnerability scanning | Detect vulnerable Python/Node dependencies | No | APPROVED |
| Dependency review | Review dependency changes in PRs | No | APPROVED |
| SBOM generation | Produce software bill of materials | No | APPROVED |
| License audit | Detect license-policy risk | No | APPROVED |
| Static code analysis / SAST | Detect unsafe code patterns | No | APPROVED |
| Django deployment/security check | Detect insecure Django deployment settings | No | APPROVED |
| Workflow policy/lint | Detect unsafe or non-compliant CI definitions | No | APPROVED |
| Compliance artifact completeness | Check required FERPA/COPPA/DPA/subprocessor/support/IR/backup docs exist | No | APPROVED |
| Release-authority marker check | Prevent unsupported GO/GA/superiority claims | No | APPROVED |

## Phase 2 — After stable sandbox runtime

Allowed only after sandbox runtime is stable, synthetic data is loaded, and owner approves the test window:

| Control | Purpose | Destructive? | Decision |
|---|---|---:|---|
| DAST against sandbox | Scan running app for web/API vulnerabilities | Low/medium | CONDITIONALLY APPROVED LATER |
| Authenticated role scanning | Verify role-scoped runtime exposure | Low/medium | CONDITIONALLY APPROVED LATER |
| API authorization scanning | Verify tenant/object permission boundaries | Low/medium | CONDITIONALLY APPROVED LATER |
| Performance/load validation | Establish system capacity and bottlenecks | Medium | CONDITIONALLY APPROVED LATER |
| Backup/restore validation | Prove recoverability | Medium | CONDITIONALLY APPROVED LATER |
| Incident-response tabletop | Prove response process | No/low | CONDITIONALLY APPROVED LATER |

## Phase 3 — Chaos engineering / fault injection

Blocked until all prerequisites are green.

Potential future chaos experiments:

| Experiment | Scope | Required safeguards |
|---|---|---|
| Database latency injection | Sandbox only | Backup/restore tested, observability active, rollback owner assigned |
| API timeout simulation | Sandbox only | Error budgets, dashboard degradation proof, incident observer assigned |
| Background job failure | Sandbox only | Queue retry proof, support notification proof |
| Email/SMS provider outage | Sandbox only | Communication fallback proof, no real recipients |
| Payment webhook failure | Sandbox/payment sandbox only | No real funds, reconciliation proof, webhook replay plan |
| Dashboard service degradation | Sandbox only | Honest unavailable/error state proof |
| Read-only database failover drill | Sandbox only | Restore/failover runbook, no production data |

## Chaos readiness prerequisites

Chaos execution is prohibited until all of the following are true:

1. Sandbox-only environment selected.
2. Synthetic data only.
3. No production secrets.
4. Backup/restore test complete.
5. Incident-response process tested.
6. Observability/incident-readiness gate green.
7. Performance/load baseline green.
8. Tenant isolation proof green.
9. RBAC/object authorization proof green.
10. Backend/frontend/Playwright gates green.
11. Dashboard provenance gate green.
12. Clear rollback plan exists.
13. Owner explicitly approves the chaos window.
14. Customer/pilot environment excluded unless separately approved in writing.
15. Final report template is prepared before experiment begins.

## Required evidence outputs

Phase 1 scanning must produce:

```text
.crown-audit/security-compliance/latest/00_SUMMARY.md
.crown-audit/security-compliance/latest/10_scan_inventory.csv
.crown-audit/security-compliance/latest/20_findings.csv
.crown-audit/security-compliance/latest/30_required_artifacts.csv
.crown-audit/security-compliance/latest/99_STATUS.json
```

Chaos-readiness checks must produce:

```text
.crown-audit/chaos-readiness/latest/00_SUMMARY.md
.crown-audit/chaos-readiness/latest/10_prerequisites.csv
.crown-audit/chaos-readiness/latest/20_blockers.csv
.crown-audit/chaos-readiness/latest/99_STATUS.json
```

## Status

Phase 1 plan: **DOCUMENTED AND APPROVED FOR NON-DESTRUCTIVE CI USE**

Chaos engineering: **NO-GO UNTIL CHAOS-READINESS GATE IS GREEN**
