# Checkpoints — Proof-of-Concept Milestones

## Gradebook Proof — Green ✅

| Field | Value |
|-------|-------|
| **Tag** | `proof-gradebook-green-20260211-0340` |
| **Commit** | e8524285 |
| **Workflow Run** | [GitHub Actions #21898088776](https://github.com/tcmegahan/Crown2026/actions/runs/21898088776) |
| **Conclusion** | ✅ SUCCESS |
| **Created** | February 11, 2026, 03:40 UTC |

### What It Proves

- ✅ **API proof**: Gradebook API endpoints (`/roster`, `/grades`, `/assignments`) return 200 OK with proper auth + school header
- ✅ **UI proof**: Dashboards UI renders the Academics roster, gradebook grid, and assignments sections without errors
- ✅ **Seed determinism**: 4-step seed pipeline (migrate → bootstrap → demo_school → academics → gradebook) produces consistent test data across runs
- ✅ **Auth contract**: Token properly captured from login response (not browser storage); sections fetched dynamically (no hardcoded UUIDs)

### Reference Docs

- [docs/CANON_CI_CONTRACT.md](CANON_CI_CONTRACT.md) — Non-negotiable CI rules (auth, seeds, ports, health checks)
- [docs/PROOF_GRADEBOOK_PLAYBOOK.md](PROOF_GRADEBOOK_PLAYBOOK.md) — How to run, diagnose failures, when to change seeds vs tests
- [docs/BRANCH_PROTECTION_SETTINGS.md](BRANCH_PROTECTION_SETTINGS.md) — How to lock main (branch protection configuration)

### How to Rollback to This Checkpoint

```bash
# Option 1: Checkout the tag
git checkout proof-gradebook-green-20260211-0340

# Option 2: Checkout the commit directly
git checkout e8524285

# Option 3: View the associated UI/API changes
git log --oneline e8524285~10..e8524285
```

---

**Note**: This checkpoint is intentionally minimal. Add new checkpoints only after green workflow + merged guardrail docs. Do not create checkpoint tags speculatively.
