# STABILIZATION GAP LIST

Pack: AUDIT_PACK_20260412_082753

## Gaps

| Area | State | Exact fix path |
|---|---|---|
| Branch protection access | GREEN | Use authenticated GitHub CLI with permission to read branch protection. This is not a repo-code fix. |
| Backend URL extraction | OPEN | Ensure django-extensions is installed and in INSTALLED_APPS, then rerun the pack. |
| Migration extraction | OPEN | Ensure Python env is healthy and manage.py showmigrations runs locally, then rerun the pack. |
| Python dependency extraction | GREEN | Ensure the audit runner can execute python -m pip freeze, then rerun the pack. |
| Health/integrity probe | GREEN | Set a valid health base URL or run local server on 127.0.0.1:8000 before rerun. |
| Deploy recency evidence | GREEN | Use authenticated GitHub CLI and corrected gh run list invocation, then rerun the pack. |

## Non-fixable in repo code
- Branch protection 403 is a permissions/integration issue.
- GitHub run history fetch requires valid GitHub CLI auth.

## Next commands
1. pwsh -File scripts/release/33_apply_stabilization_fixes.ps1
2. pwsh -File scripts/release/34_rerun_stabilization_audit.ps1