# Security Gates Evidence

Generated: 2026-04-02

This document records the current evidence state for CodeQL, dependency audit, and secret scanning controls.

## Security Gates Summary

| Gate | Workflow | Config Exists | Blocking Evidence in Repo | Current Status |
|---|---|---|---|---|
| CodeQL | `.github/workflows/codeql.yml` | Yes | No PR screenshot/log proving required blocking behavior | `PARTIAL` |
| Dependency audit | `.github/workflows/dependency-audit.yml` | Yes | No PR screenshot/log proving blocking behavior | `PARTIAL` |
| Secret scan | `.github/workflows/secret-scan.yml` | Yes | No PR screenshot/log proving blocking behavior | `PARTIAL` |

## Detailed Evidence

### CodeQL

- Present:
  - Workflow file: `.github/workflows/codeql.yml`
- Missing:
  - `docs/release/security-gate-evidence/codeql-blocking-evidence.png`
- Blocking state:
  - `MANUAL_VERIFICATION_REQUIRED` against live branch protection settings.

### Dependency Audit

- Present:
  - Workflow file: `.github/workflows/dependency-audit.yml`
- Missing:
  - `docs/release/security-gate-evidence/dep-audit-blocking-evidence.png`
- Blocking state:
  - `MANUAL_VERIFICATION_REQUIRED` against live branch protection settings.

### Secret Scan

- Present:
  - Workflow file: `.github/workflows/secret-scan.yml`
- Missing:
  - `docs/release/security-gate-evidence/secret-scan-blocking-evidence.png`
- Blocking state:
  - `MANUAL_VERIFICATION_REQUIRED` against live branch protection settings.

## Supporting Audit Evidence

- `AUDIT_PACK_20260330_193349/10_SECRET_SCAN_FINDINGS.txt`
  - Contains: `gitleaks not installed`
  - Interpretation: no captured scan output in that evidence pack; additional capture required.

## Required Follow-Up to Prove Blocking Behavior

1. Create a controlled PR that triggers each gate.
2. Capture failed-check screenshots proving merge blocking behavior.
3. Store screenshots in `docs/release/security-gate-evidence/`.
4. Update `docs/release/FINAL_INVESTOR_EVIDENCE_INDEX.md` statuses from `MISSING` to `PRESENT`.

## Status

Current status: `PARTIAL`  
Reason: workflows exist, but direct evidence of blocking enforcement is not yet committed.
