# Branch Protection Evidence

Generated: 2026-04-11

This document records the live `main` branch-protection proof currently committed in-repo and the small amount of evidence that still requires manual capture.

## Required Checks on `main`

From the live API export committed at `docs/release/branch-protection-export.json`, required checks currently include:

- `CodeQL`
- `changes`
- `demo-proof-static`
- `demo-surface-static-gate`
- `lockdown-gate`
- `meta-check-job-if`
- `phase1-contract`
- `phase3-runtime-proof`
- `proof-ceremony`
- `pytest`
- `rc-promotion-gate`
- `spine-audit`
- `test`
- `verify-immutable-tags`

This list now reflects the live GitHub API state, including the corrected CodeQL context (`CodeQL`) that matches the currently emitted GitHub Advanced Security check.

## Evidence Matrix

| Control | Evidence Present? | Evidence Path | Notes |
|---|---|---|---|
| Branch protection export file exists | Yes | `docs/release/branch-protection-export.json` | Live API export for `main` |
| Branch protection screenshot exists | No | `docs/release/security-gate-evidence/branch-protection-screenshot.png` | Optional/manual screenshot capture still pending |
| Required checks list documented | Yes | `docs/release/branch-protection-export.json` | Shows 14 live required checks including `CodeQL` |
| Admin enforcement proven | Yes | `docs/release/branch-protection-export.json` | `enforce_admins.enabled: true` |
| Force pushes disabled proven | Yes | `docs/release/branch-protection-export.json` | `allow_force_pushes.enabled: false` |
| Deletions disabled proven | Yes | `docs/release/branch-protection-export.json` | `allow_deletions.enabled: false` |
| Code owner review expected/proven | Yes | `docs/release/branch-protection-export.json` | `require_code_owner_reviews: true` |
| Conversation resolution expected/proven | Yes | `docs/release/branch-protection-export.json` | `required_conversation_resolution.enabled: true` |
| Linear history expected/proven | No | `docs/release/branch-protection-export.json` | `required_linear_history.enabled: false` |

## Remaining Manual Capture from GitHub Settings

1. Open repository settings for branch protection on `main`.
2. Capture a UI screenshot covering:
   - Required status checks
   - Require pull request before merging
   - Required approvals and stale review dismissal
   - Require code owner review
   - Require conversation resolution
   - Restrict force pushes and deletions
   - Enforce for administrators
3. Commit the screenshot to `docs/release/security-gate-evidence/` if the investor bundle still needs a UI artifact.

## Status

Current status: `PARTIAL`  
Reason: the live API export is now accurate and current; only the optional GitHub UI screenshot is still missing.
