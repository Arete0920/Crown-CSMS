# Branch Protection Evidence

Generated: 2026-04-02

This document records branch-protection proof currently available in-repo and what still requires manual capture.

## Expected Required Checks

From the live audit-pack export committed at `docs/release/branch-protection-export.json`, required checks currently include:

- `proof-ceremony`

Phase 2 governance analysis identifies additional checks that should be required (documented in `docs/repo-cleanup/REQUIRED_CHECKS_MAP_PHASE2.md`) but are not yet proven configured as required in live GitHub settings.

## Evidence Matrix

| Control | Evidence Present? | Evidence Path | Notes |
|---|---|---|---|
| Branch protection export file exists | Yes | `docs/release/branch-protection-export.json` | Snapshot copied from in-repo ruleset, not live API fetch |
| Branch protection screenshot exists | No | `docs/release/security-gate-evidence/branch-protection-screenshot.png` | Manual screenshot capture required |
| Required checks list documented | Yes | `docs/release/branch-protection-export.json` | Shows `proof-ceremony` only |
| Admin enforcement proven | No | — | Manual GitHub settings confirmation required |
| Force pushes disabled proven | No | — | Manual GitHub settings confirmation required |
| Deletions disabled proven | Partial | `docs/release/branch-protection-export.json` | Ruleset includes `deletion`; live setting still requires UI/API verification |
| Code owner review expected/proven | Partial | `docs/release/branch-protection-export.json` | Snapshot shows `require_code_owner_review: false`; manual policy decision required |
| Conversation resolution expected/proven | Partial | `docs/release/branch-protection-export.json` | Snapshot shows `required_review_thread_resolution: false`; manual policy decision required |
| Linear history expected/proven | No | — | Not evidenced in current snapshot; manual verification required |

## Manual Capture Required from GitHub Settings

1. Open repository settings for branch/ruleset protection on `main`.
2. Export or capture screenshots covering:
   - Required status checks
   - Require pull request before merging
   - Required approvals and stale review dismissal
   - Require code owner review
   - Require conversation resolution
   - Restrict force pushes and deletions
   - Enforce for administrators
   - Require linear history
3. Commit screenshot(s) to `docs/release/security-gate-evidence/`.
4. Replace or supplement `docs/release/branch-protection-export.json` with live export output.

## Status

Current status: `PARTIAL`  
Reason: ruleset snapshot exists, but live GitHub settings proof package is incomplete.
