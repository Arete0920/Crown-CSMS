# Problems Panel Classification Inventory

## Rule

Classification only. No fixes in this branch until categories, owners, and priorities are recorded.

## Categories

1. YAML workflow parse/blockers
2. Python runtime/test blockers
3. Frontend test/lint blockers
4. CSS warnings
5. Markdownlint documentation noise
6. Duplicate workspace/path noise

## Classification Table

| # | Category | Count | Representative Files | Release Blocking? | Owner | Next Action |
|---|---|---:|---|:---:|---|---|
| 1 | YAML workflow parse/blockers | ~14 parse errors (active workspace); ~7 workflows with unresolved-action version errors (stale clones) | `.github/workflows/prod-health-watch.yml` (heredoc `<<'PY'` confuses YAML parser — 14 errors); `release-verify.yml`, `schema-governance.yml` (unresolved action version pins — stale clone only) | No (errors are in local `Crown2026_deploypr` copy, not `crown_main_postmerge_verify`; CI passes) | TC | Confirm which errors are active-workspace vs stale-clone artifacts; no CI fix required unless check fails |
| 2 | Python runtime/test blockers | 0 confirmed errors (1,198 .py files scanned; all returned "No errors found") | None | No | TC | Re-validate after next pytest run; no action pending |
| 3 | Frontend test/lint blockers | 14 spec files with selector-based assertions; 1 previously broken (`executive-dashboard-v1.spec.ts`, fixed in PR #757) | `frontend/dashboards/tests/ui/executive-dashboard-v1.spec.ts` (fixed), `frontend/dashboards/tests/ui/dashboard-proof.spec.ts`, `frontend/dashboards/tests/ui/gradebook-ui-proof.spec.ts` | Was blocking (PR #757); now green | TC | Run `npx playwright test` to get fresh post-fix failure count before marking resolved |
| 4 | CSS warnings | 3 duplicate selectors across 2 files | `frontend/dashboards/src/styles/crown.css` (`.crown-main` L91/L266; `.crown-btn-primary` L175/L281); `frontend/dashboards/src/styles/crown-theme.css` (`.crown-btn-primary` L92/L206) | No | TC/Frontend | Deduplicate after classification approved; do not fix until table is reviewed |
| 5 | Markdownlint documentation noise | 458 trailing-space violations across 523 .md files | `.github/copilot-instructions.md`, `.github/pull_request_template.md`, `docs/BUILD_RULES.md`, `docs/ADMISSIONS_INTEGRATION_COMPLETE.md`, `core_shadowed/README.md` | No | TC/Documentation | Bulk auto-fix with `markdownlint --fix` after classification approved |
| 6 | Duplicate workspace/path noise | 6 local workspace clones under `C:\w\` generating false-positive Problems Panel hits | `C:\w\crown_pr756_replacement` (~20 unresolved-action errors), `C:\w\pr756_fix`, `C:\w\pr756_repair`, `C:\w\crown_main_validation_hotfix`, `C:\w\crown_main_verify` | No | TC | Remove stale workspace folders from VS Code workspace list to eliminate noise; do not delete git history |

## Summary

| Category | Count | Blocking | Priority |
|---|---:|:---:|---|
| YAML parse/blockers (active workspace) | 0 CI-blocking | No | Low — stale-clone noise only |
| Python runtime/test blockers | 0 | No | None pending |
| Frontend test/lint blockers | 14 spec files (1 fixed) | Was / Now green | Medium — confirm post-fix |
| CSS warnings | 3 duplicate selectors | No | Low |
| Markdownlint noise | 458 trailing spaces | No | Low — bulk fix eligible |
| Duplicate workspace noise | 5 stale clones | No | Medium — close to clear panel |

## Non-Negotiables

- Do not change release authority files.
- Do not modify Gate 4 records.
- Do not reopen PR #756/#757/#760.
- Do not fix diagnostics until classification is reviewed and approved.

## Classification Date

2026-04-25
