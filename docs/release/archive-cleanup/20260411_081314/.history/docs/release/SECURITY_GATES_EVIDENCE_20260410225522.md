# Security Gates Evidence

Generated: 2026-04-11

This document records the current evidence state for CodeQL, dependency audit, and secret scanning controls.

## Security Gates Summary

| Gate | Workflow / Control | Config Exists | Blocking Evidence in Repo | Current Status |
|---|---|---|---|---|
| CodeQL | `GitHub Advanced Security default setup` | Yes | Live API evidence committed at `docs/release/security-gate-evidence/codeql-live-state.txt`; UI screenshot still not committed | `PARTIAL` |
| Dependency audit | `.github/workflows/dependency-audit.yml` | Yes | No PR screenshot/log proving blocking behavior | `PARTIAL` |
| Secret scan | `.github/workflows/secret-scan.yml` | Yes | No PR screenshot/log proving blocking behavior | `PARTIAL` |

## Detailed Evidence

### CodeQL

- Present:
  - `docs/release/security-gate-evidence/codeql-live-state.txt`
  - Live GitHub API verification shows CodeQL default setup is `configured` with weekly schedule.
  - A recent PR head emitted a successful `CodeQL` check from `github-advanced-security`.
  - `main` branch protection has been corrected to require `CodeQL` so the required context now matches the live emitted check.
- Missing:
  - `docs/release/security-gate-evidence/codeql-blocking-evidence.png` (optional UI screenshot only)
- Blocking state:
  - `LIVE_API_VERIFIED`; screenshot capture is still optional/manual for the evidence bundle.

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

- `docs/release/security-gate-evidence/codeql-live-state.txt`
  - Contains: live `gh api` capture for default setup state, required checks on `main`, and a successful PR `CodeQL` check.
- `AUDIT_PACK_20260330_193349/10_SECRET_SCAN_FINDINGS.txt`
  - Contains: `gitleaks not installed`
  - Interpretation: no captured secret-scan output in that older evidence pack; additional capture required.

## Remaining Manual Capture (Optional for investor bundle)

1. Capture UI screenshots for CodeQL, dependency audit, and secret scan blocking behavior.
2. Store screenshots in `docs/release/security-gate-evidence/`.
3. Update `docs/release/FINAL_INVESTOR_EVIDENCE_INDEX.md` if those screenshots are added.

## Status

Current status: `PARTIAL`  
Reason: live API evidence now confirms CodeQL is configured and aligned with branch protection, but the optional screenshot package is still incomplete.
