# Prod Bootstrap, ACR Pin, and Credential Rotation

**Date:** 2026-03-02  
**Branch:** `fix/system-wiring-and-test-fixes` (PR #502)  
**HEAD at close:** `4807c9916edcfc7522578a5d5a98f450e44cb398`  
**Recorded source:** owner-directed operations tooling

## Historical purpose

This record documents a March 2, 2026 production bootstrap and credential-rotation session. It is retained for operational chronology only and is not current release authority.

## Actions recorded

- rotated the exposed PostgreSQL application credential;
- rotated the Django administrative credential;
- retained an idempotent administrative bootstrap path;
- built and pinned the container image tag `crown2026:20260302b`;
- updated the deployed `BUILD_SHA` to `4807c9916edcfc7522578a5d5a98f450e44cb398`;
- added `CROWN_ENV=prod` to correct the production health-environment signal;
- restarted the application and verified health and authentication paths;
- confirmed local secret files remained excluded from Git.

## Security boundary

All command examples and credential values from the original session are intentionally omitted from this retained summary. Live credentials, tokens, and connection strings must remain outside repository records.

## Historical findings

The session identified these then-current concerns:

- application use of a server-level database administrative account;
- build identity not baked into the image by the original build path;
- a hardcoded development secret-key fallback;
- possible cold-start timing risk around migrations.

These observations are historical. Current disposition must be verified against current code, deployed configuration, issue `#1619`, and `docs/CURRENT_RELEASE_STATUS.md`.

## Authority boundary

Development tooling may support implementation, analysis, and evidence capture. Tool output does not constitute independent human review, approval, certification, or release authority.
