# CROWN Security Scripts

This directory contains scripts and modules for safe credential handling, redacted command execution, repository hygiene, and operational verification.

## Secret-handling rules

- Never place live credentials, tokens, connection strings, or private keys in repository files, issue comments, pull requests, chat transcripts, or retained evidence.
- Use environment variables, approved secret stores, or ignored local secret files.
- Redact outputs before sharing them with any person, tool, connector, or support channel.
- Confirm secret existence with boolean or name-only queries rather than dumping values.
- Rotate any credential that may have been exposed and verify the old credential is invalid.

## Retired predecessor operations

The following predecessor-era and unguarded operations have been retired from the active script tree: `scripts/ops/run_migrations_remote.ps1`, `scripts/ops/run_migrations_dev.ps1`, `scripts/provision_ci_user_dev_azure.sh`, `scripts/recovery/run_revised_48h_sprint.ps1`, and `scripts/recovery/run_maximum_proof_sprint.ps1`. The legacy remote script targeted a retired Azure hostname; the direct DEV migration helper targeted the current app but lacked exact-source, database-recovery and rollback guards; the CI-user helper generated a password-reset script without a controlled deployment path; and the recovery helpers retained obsolete source or execution assumptions. Their original contents remain in Git history for provenance only, not execution.

For current DEV migrations and deployment, use the protected repository workflows and the exact-source/authorization requirements in [current release status](../docs/CURRENT_RELEASE_STATUS.md) and [operations](../docs/operations/README.md). Do not recreate the old ad hoc commands or bypass the queued-run incident under issue #427.

## Core utilities

### `Redact.psm1`

Provides redaction helpers for passwords, tokens, connection strings, authorization headers, and project-specific secret patterns.

### `Invoke-SecureCommand.ps1`

Runs commands while redacting sensitive output. Raw-output bypasses are prohibited unless the output is independently verified as non-sensitive.

### `ops/root_legacy/`

Contains retained legacy helper scripts moved from the repository root. These helpers are not current release authority and must be used only when their behavior and dependencies are verified.

## Sharing command evidence

Before pasting output into any communication or evidence channel:

1. remove secret values;
2. remove personal or customer data;
3. retain only the fields needed to prove the result;
4. identify the command, evaluated SHA, environment, and timestamp where relevant;
5. confirm the sanitized output cannot be used to reconstruct credentials.

## Pre-commit protection

Secret scanning must run before commit. Do not bypass a secret-scanning hook or required repository check. Remove the sensitive value, rotate it where necessary, and recommit cleanly.

## Authority boundary

Development tooling may support inspection, implementation, testing, analysis, and evidence organization. Tool output does not constitute independent human review, approval, certification, or release authority.
