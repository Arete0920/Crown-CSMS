# Demo Proof Process Canon (pp-003)

## Release Policy (Frozen Tag, Moving Docs)

**Demo tag is a frozen release:**
- `demo-feb16-gradebook-edit-pp-003` pinned to proven SHA (`aec71930`)
- **Tag does not move after initial validation** (until after Feb 16 demo)
- This is standard practice: release tags are immutable until release is over

**Main branch can advance independently:**
- Docs, proof artifacts, and scripts can be added to main without retagging
- Code changes require PR + CI (never direct-to-main)
- Docs may use PR or direct-to-main (team chooses)

**No retagging to include docs commits** — tags capture code, not documentation

---

## Workflow for Code Changes (Code = Always PR)

## Workflow for Code Changes (Code = Always PR)

1. `git checkout main && git pull`
2. `git checkout -b fix/<topic>`
3. Make changes, test locally
4. `git commit -m "type(scope): description"`
5. `git push -u origin fix/<topic>`
6. `gh pr create -R tcmegahan/Crown2026 --base main --head fix/<topic> ...`
7. Wait for CI checks to pass
8. `gh pr merge <branch> -R tcmegahan/Crown2026 --admin --squash --delete-branch`
9. `git checkout main && git pull origin main`
10. ~~`git tag -f demo-feb16-gradebook-edit-pp-003 origin/main`~~ **← Do NOT retag**
11. ~~`git push -f origin demo-feb16-gradebook-edit-pp-003`~~ **← Tag stays frozen**

## Why This Matters

**Frozen Release Tags (Industry Standard):**
- Tags capture a specific, validated code state
- They do not move after release validation begins
- Docs and artifacts live in main but do not affect tag SHA

**This Protects the Demo:**
- Investor receives tag SHA (immutable proof)
- Tag points to proven hardening commit (aec71930)
- No accidental code drift into "demo" state
- Docs can improve independently without invalidating proof

## Proof Definition

**Acceptance test:**
- Two consecutive runs of `demo_boot_feb16.ps1` **from the demo tag**
- **No manual process kills between runs** (port management automated)
- Boot script exits code 0 both times
- Logs show `[OK] Demo Boot Complete` in both PROOF_RUN1.log and PROOF_RUN2.log

**Scripts:**
- `RUN_PROOF_NO_MANUAL_CLEANUP.ps1` — Auditable proof (no intervention needed)
- `RUN_RESET_AND_BOOT_TWICE.ps1` — For local reset-and-verify (manual kills OK)

## If You Break This Rule

Do not rewrite history. Instead:
- Document the infraction
- Create a new PR for all changes
- Re-run proof
- Re-tag to the new commit

---

**Last Updated:** 2026-02-13
**Last Enforced:** demo-feb16-gradebook-edit-pp-003 acceptance run
