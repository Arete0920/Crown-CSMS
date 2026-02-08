# SPINE EXECUTION CONTRACT (Crown2026)

This contract defines the execution rules for VS Code + GitHub workflow changes to prevent "blast radius creep," hidden regressions, and wandering.

## 1) Non-Negotiables

- **One PR = one purpose.**
- **Blast radius must be declared before edits.**
- **No "helpful extra fixes."** If it's not in the blast radius, it does not change.
- **Proof is raw output.** No interpretations in the proof section.
- **If anything unexpected happens, STOP** and return to the contract.

## 2) Blast Radius Rule

Every PR must include an explicit allowed list:
- Allowed files/dirs (exact paths)
- Everything else is **forbidden**

If a tool or editor changes something outside the allowed list:
1. `git checkout -- <file>` (revert)
2. Re-check blast radius
3. Continue only when clean

## 3) Deterministic Execution Pattern

Always run commands in this order and paste raw output:

1. `git status -sb`
2. `git diff --stat`
3. Run the smallest local proof:
   - backend: `python backend/manage.py check`
   - tests: run only the relevant test file(s) if full suite is known flaky, but CI must be green
4. Commit (single purpose message)
5. Push branch
6. PR
7. Watch checks to completion
8. Merge only when policy satisfied

## 4) Required Proof Gates

### Local Proof (minimum)
- `git status -sb`
- `git diff --stat`
- `python backend/manage.py check`

### CI Proof (must be green)
- pytest
- Spine Audit (Canon Guard)
- Proof Ceremony
- Secret Scan
- CI - Tests and Checks

## 5) Deploy Determinism Rule

For any deploy-related PR or production deploy:
- App must expose `build_sha` on `/health/`
- Workflow must set `BUILD_SHA=${{ github.sha }}`
- Workflow must hard-verify:
  - log contains `OK build_sha: <sha>`
  - if mismatch  deploy fails (no silent success)

## 6) Communication Rule (for agents/tools)

When instructing an agent (Copilot Chat, ChatGPT, etc.), the instruction must be:
- Exact file paths
- Exact code blocks to paste
- Exact commands to run (in order)
- Expected outputs (where applicable)
- A hard **stop** point

## 7) Definition of "Done"

A task is done only when:
- Blast radius clean
- Local proof clean
- CI proof green
- If deploy-related: determinism verified via `/health/`
