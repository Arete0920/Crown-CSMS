# PR Triage — Phase 2

Generated: Phase 2 cleanup pass  
Branch: `chore/github-cleanup-phase2-workflows-prs`  
Active open PRs surveyed: 16

## Triage Labels

| Label | Meaning |
|---|---|
| `MERGE_NEXT` | Ready or near-ready; unblock and merge soon |
| `NEEDS_REBASE` | Behind main; rebase required before merge |
| `NEEDS_REVIEW` | No review yet; assign and review |
| `NEEDS_CONFLICT_RESOLUTION` | Merge conflict (DIRTY state); resolve before proceeding |
| `DEFER` | Valid work but not urgent; defer to next sprint |
| `CLOSE_STALE` | Superseded, abandoned, or unreachable path; close without merging |

---

## PR Triage Table

| # | Title | Branch | Author | Created | Checks | Decision | Notes |
|---|---|---|---|---|---|---|---|
| 641 | chore: remove stale operational debris from repo root | `release-readiness/chore-cleanup-root` | tcmegahan | 2026-04-01 | BLOCKED | `CLOSE_STALE` | Phase 1 cleanup is now covered by `chore/github-cleanup-phase1` with a superior commit (`e26a77fb`); this PR is a stale predecessor |
| 640 | docs: commit governance and documentation package for investor review | `release-readiness/docs-governance-package` | tcmegahan | 2026-04-01 | BLOCKED | `MERGE_NEXT` | Governance docs for investor review — high value; unblock after checking what checks are blocking |
| 639 | feat(ci): add blocking pip-audit + npm audit dependency workflow | `release-readiness/security-dependency-audit` | tcmegahan | 2026-04-01 | BLOCKED | `MERGE_NEXT` | Adds `dependency-audit.yml` which is classified KEEP_CANONICAL; important security gate |
| 638 | fix(security): remove continue-on-error from CodeQL — now blocking | `release-readiness/security-codeql-blocking` | tcmegahan | 2026-04-01 | BLOCKED | `MERGE_NEXT` | Hardens CodeQL from informational → blocking; aligns with Phase 3 required checks recommendation |
| 637 | fix(ci): repair malformed heredoc in prod-health-watch.yml | `release-readiness/ci-prod-health-watch-fix` | tcmegahan | 2026-04-01 | BLOCKED | `MERGE_NEXT` | Fixes production health watch workflow; operational reliability fix |
| 636 | chore: bulk remove tracked generated artifacts and non-canonical root files | `copilot/bulk-remove-non-canonical-files` | copilot-swe-agent | 2026-04-01 | BLOCKED (`REVIEW_REQUIRED`) | `NEEDS_REVIEW` | Copilot agent PR; review diff carefully — cannot merge blindly; verify it doesn't remove needed files |
| 635 | enforce: lock down main branch protection and repo policies | `copilot/enforce-branch-protection-policies` | copilot-swe-agent | 2026-04-01 | BLOCKED (`REVIEW_REQUIRED`) | `NEEDS_REVIEW` | Copilot agent PR; branch protection changes are high-impact — review all changes before merging |
| 632 | feat: parent portal my-student consolidation | `feat/parent-portal-consolidation` | tcmegahan | 2026-03-31 | BLOCKED (`REVIEW_REQUIRED`) | `NEEDS_REVIEW` | Feature work; review and approve |
| 630 | feat(billing): automated invoicing + CompuWerx webhook + late fees | `feat/billing-compuwerx` | tcmegahan | 2026-03-31 | BLOCKED | `NEEDS_REVIEW` | Billing feature; no review yet |
| 629 | feat(financial-aid): complete all 5 director actions + application intake | `feat/financial-aid-complete` | tcmegahan | 2026-03-31 | BLOCKED | `NEEDS_REVIEW` | Financial aid feature; canonical module — should merge before related work |
| 628 | feat(little-lambs): complete Little Lambs daycare module | `feat/little-lambs-module` | tcmegahan | 2026-03-31 | BEHIND | `NEEDS_REBASE` | Behind main; rebase then review |
| 626 | feat(audit-roadmap): phases 3-5 quality, operations, and feature completeness | `feat/test-coverage-infrastructure` | tcmegahan | 2026-03-31 | BEHIND | `NEEDS_REBASE` | Roadmap doc PR; rebase then merge |
| 625 | feat(security): complete security hardening (Phase 2 of A+ Audit Roadmap) | `feat/security-headers` | tcmegahan | 2026-03-31 | BEHIND (`REVIEW_REQUIRED`) | `NEEDS_REBASE` | Security hardening; high value — rebase and complete review |
| 618 | fix: restore deploy test contracts (dashboards + tenant endpoints) | `fix/allowed-hosts-testserver` | tcmegahan | 2026-03-28 | BEHIND | `NEEDS_REBASE` | Contract restore fix; rebase required |
| 611 | ci: guard CodeQL and dependency review when security features are unavailable | `ci/security-feature-gate-guard` | tcmegahan | 2026-03-28 | DIRTY (conflict) | `NEEDS_CONFLICT_RESOLUTION` | Merge conflict; resolve then re-review |
| 600 | chore(ci): harden production deploy trigger and environment protections | `chore/deploy-trigger-hardening-clean` | tcmegahan | 2026-03-20 | DIRTY (conflict) | `NEEDS_CONFLICT_RESOLUTION` | Oldest open PR; CI hardening work; significant conflict risk — resolve or close and re-open |

---

## Priority Merge Order

For unblocking production readiness fastest, recommended merge sequence:

1. **#637** — Fix prod-health-watch heredoc (no risk, fix only)
2. **#638** — CodeQL blocking (security hardening, low risk)
3. **#639** — Dependency audit workflow (adds `dependency-audit.yml`)
4. **#640** — Governance docs (investor-facing, no code)
5. **#629** — Financial aid complete (canonical module, high value)
6. **#625** — Security headers hardening *(after rebase)*
7. **#632** — Parent portal consolidation *(after review)*
8. **#630** — Billing/invoicing *(after review)*
9. **#628** — Little Lambs *(after rebase)*
10. **#626** — Audit roadmap docs *(after rebase)*
11. **#636** — Copilot bulk remove *(review diff very carefully first)*
12. **#635** — Copilot branch protection *(review very carefully — high blast radius)*
13. **#618** — Deploy test contracts *(after rebase)*

**Conflict-resolution required before any merge decision:**
- #611 (security feature gate guard)
- #600 (deploy trigger hardening)

**Close without merging:**
- #641 — Superseded by the Phase 1 cleanup already committed to `chore/github-cleanup-phase1`

---

## Copilot-Agent PR Risk Notes

PRs #635 and #636 were opened by `copilot-swe-agent`. These require additional scrutiny:

- **#635 (branch-protection):** Any changes to `ruleset_main.json`, CODEOWNERS, or `.github/` governance files must be reviewed line-by-line. Incorrect branch protection changes can lock out all merges or silently remove guards.
- **#636 (bulk-remove):** Any bulk removal of tracked files must be verified against the file inventory. Files like `docs/RELEASE_TAGS.json`, workflow files, and backend source must not be deleted.

---

## Summary

| Category | Count |
|---|---|
| MERGE_NEXT | 4 (after checks clear) |
| NEEDS_REVIEW | 6 |
| NEEDS_REBASE | 4 |
| NEEDS_CONFLICT_RESOLUTION | 2 |
| CLOSE_STALE | 1 |
| **Total** | **17** |
