# Crown2026 — Open Questions

## Purpose

This file lists the questions that are still unanswered, blocked, or newly answered.

Each question must be marked:
- Answered
- Open
- Blocked

---

## Open Questions Table

| ID | Question | Status | Owner | Evidence / Answer | Next Action |
|---|---|---|---|---|---|
| Q-001 | Which exact SHA is the current release-candidate truth? | Blocked | Release owner | RC artifact file missing; no RC build_sha available | Produce/recover release-candidate.json and bind build_sha to SHA |
| Q-002 | Which SHA is currently deployed to frontend production? | Open | Release owner | No frontend deploy probe captured in this snapshot | Run deploy probe and record URL + SHA |
| Q-003 | Which SHA is currently deployed to backend production? | Open | Backend owner | No production backend deploy probe captured in this snapshot | Capture production backend /api/health equivalent and compare |
| Q-004 | Which modules are actually complete versus merely present? | Open | Module owners | Module matrix still largely UNPROVEN | Populate module evidence and exit criteria |
| Q-005 | Which investor demo flows are certified? | Open | Demo owner | Local smoke flows passed; investor script not formally certified | Attach certified demo script + evidence packet |
| Q-006 | Which finance flows are fully proven? | Open | Finance owner | No current finance proof artifact linked in completion docs | Run/link finance proof artifacts on current SHA |
| Q-007 | Which security findings remain open? | Open | Security owner | CodeQL merge gate is green on PR 577; outstanding finding inventory still needs explicit security packet | Document remaining findings disposition from security/code-scanning views |
| Q-008 | Which branches contain unmerged critical work? | Open | Release owner | Open PR list includes multiple adjacent fix branches (#578/#579/#580) | Triage open PRs and mark release relevance |
| Q-009 | Which proof routes are canonical and which are aliases? | Answered | Frontend owner | Route and proof contracts were reconciled during PR 577 stabilization and reflected in completion docs | Keep route/proof contract synced with router changes |
| Q-010 | What is the exact current blocker set for release? | Answered | Release owner | Branch-level blockers for PR 577 are closed; remaining blockers are release-wide (RC artifact + deployed truth + module/investor evidence) | Keep ledger in sync with every CI refresh |

---

## Newly Added Questions

| ID | Question | Status | Owner | Evidence / Answer | Next Action |
|---|---|---|---|---|---|
| Q-011 | Is PR #577 merge-ready right now? | Answered | Release owner | Yes; PR 577 merged to main at 2026-03-15T20:59:18Z | None |
| Q-012 | Is backend health endpoint currently reachable in local dev? | Answered | Backend owner | Yes, /api/health returned status ok payload | Keep endpoint truth in 00-CURRENT-TRUTH |

---

## Answered Questions Archive

### Q-
- Question:
- Answer:
- Evidence:
- Date answered:
- Notes:

### Q-010
- Question: What is the exact current blocker set for release?
- Answer: PR 577 branch-level blockers are resolved; remaining blockers are missing RC artifact and unresolved deployment/module/investor proof gaps.
- Evidence: docs/completion/03-BLOCKER-LEDGER.md and PR 577 statusCheckRollup
- Date answered: 2026-03-15
- Notes: Re-evaluate after each CI run.

### Q-011
- Question: Is PR #577 merge-ready right now?
- Answer: Yes; merge is complete.
- Evidence: PR 577 merged, merge commit 550d84b23dbfb85cdbc5a75705110d691ac8eca9
- Date answered: 2026-03-15
- Notes: Closed as answered by merge event.

### Q-012
- Question: Is backend health endpoint currently reachable in local dev?
- Answer: Yes, /api/health responds with status ok.
- Evidence: local probe output in snapshot run
- Date answered: 2026-03-15
- Notes: This does not prove production health.

---

## Notes

- Questions are evidence-scoped to this snapshot only.
- Production questions remain open unless explicit production probes are linked.
- Blocked status is reserved for questions awaiting missing prerequisite artifacts.
