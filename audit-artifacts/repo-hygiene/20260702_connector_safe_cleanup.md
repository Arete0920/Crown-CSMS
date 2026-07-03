# Connector-Safe Repo Hygiene Cleanup — 2026-07-02

Branch: `chore/root-hygiene-connector-20260702`
Scope: low-risk text/config hygiene only

## Purpose

Reduce immediate dirty-hygiene risk that can be safely handled through the GitHub connector without bulk file moves/deletions or local workflow validation.

This is not release approval, sandbox approval, pilot approval, or production approval.

## Changes applied

1. `.env.example`
   - Removed stale UTF-8 BOM from the file content.
   - Repointed `DJANGO_SETTINGS_MODULE` from `crown2026_config.settings` to `crown_api.settings`.

2. `.gitignore`
   - Normalized mojibake comments into plain ASCII comments.
   - Deduplicated common generated-noise rules.
   - Added explicit hygiene rules for:
     - `check_output*.txt`
     - `**/workflow-logs/`
   - Preserved existing generated artifact and local secret ignore intent.

## Connector inspection findings

A search for `crown2026_config` still shows references outside `.env.example`, including:

- `crown2026_config/wsgi.py`
- `crown2026_config/urls.py`
- `crown2026_config/settings.py`
- `crown2026_config/asgi.py`
- release scripts and historical docs/artifacts

Because the GitHub connector cannot run the required local `git grep` and Django validation gates, this branch does not delete `crown2026_config/` or bulk-move historical folders.

## Explicitly not done

- No evidence purge.
- No root historical document archive.
- No deletion of `crown2026_config/`.
- No deletion of current/latest/state authority evidence.
- No coverage-truth change.
- No auth/login runtime repair.
- No production, sandbox, or pilot approval.

## Required local validation before merge

```powershell
python manage.py check
python backend/manage.py check
git grep -n "crown2026_config"
git grep -n "01_backend_full_gate.ps1\|80_runner_recovery_rerun_pack.ps1\|APPLY_DEMO_PROOF_FIXES.ps1\|APPLY_WIRING_VERIFICATION_PACK.ps1" .github/workflows docs scripts
```

## Remaining hygiene punch list

1. Finish PR-1 root cleanup locally with workflow grep support.
2. Decide whether `crown2026_config/` is live fallback or stale residue.
3. Archive stale root historical docs under `docs/release/archive/root-legacy-20260702/` only after reference checks.
4. Run PR-2 evidence slim only after pre-purge tag and external archive location are recorded.
5. Run PR-3 coverage truth after hygiene PRs are settled.

## Status

Partial connector-safe cleanup complete. Full dirty-hygiene cleanup remains open under issue #1235.
