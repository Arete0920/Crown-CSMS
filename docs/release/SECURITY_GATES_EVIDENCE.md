<!-- markdownlint-disable MD060 -->

# Security Gates Evidence

Authority Scope Notice (2026-05-29)

This document is a security evidence artifact and not a controlling repository-level release authority source.

Current controlling release-authority sources:

- docs/CURRENT_RELEASE_STATUS.md
- docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

Generated: 2026-04-11

This document records the current evidence state for CodeQL, dependency audit, and secret scanning controls.

## Security Gates Summary

| Gate | Workflow / Control | Config Exists | Blocking Evidence in Repo | Current Status |
|---|---|---|---|---|
| CodeQL | `GitHub Advanced Security default setup` | Yes | Live API evidence committed at `docs/release/security-gate-evidence/codeql-live-state.txt`; `main` requires the live `CodeQL` check | `LIVE_API_VERIFIED` |
| Dependency audit | `.github/workflows/dependency-audit.yml` | Yes | Live branch protection now requires `dependency-review`, `Backend Python Dependency Audit`, and `Frontend Node Dependency Audit`; local audit remediation is current | `LIVE_REQUIRED_CHECK` |
| Secret scan | `.github/workflows/secret-scan.yml` | Yes | Live branch protection now requires `secret-scan`, and recent PR checks emitted the gate successfully | `LIVE_REQUIRED_CHECK` |

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
  - Live branch protection export now requires `dependency-review`, `Backend Python Dependency Audit`, and `Frontend Node Dependency Audit`.
  - Local remediation is verified: backend Django was updated from `5.2.12` to `5.2.13`, `pip_audit` now reports no known vulnerabilities, and the frontend lockfile was refreshed so `npm audit` reports 0 vulnerabilities.
- Missing:
  - `docs/release/security-gate-evidence/dep-audit-blocking-evidence.png` (optional UI screenshot only)
- Blocking state:
  - `LIVE_REQUIRED_CHECK`; screenshot capture remains optional/manual for the investor bundle.

### Secret Scan

- Present:
  - Workflow file: `.github/workflows/secret-scan.yml`
  - Live branch protection export now requires `secret-scan` on `main`.
  - Recent PR checks emitted `secret-scan` successfully, confirming the gate name and workflow surface are live.
- Missing:
  - `docs/release/security-gate-evidence/secret-scan-blocking-evidence.png` (optional UI screenshot only)
- Blocking state:
  - `LIVE_REQUIRED_CHECK`; screenshot capture remains optional/manual for the investor bundle.

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
