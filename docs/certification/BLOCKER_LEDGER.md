# Crown2026 Blocker Ledger

> **Superseded authority notice (2026-10-05):** This blocker ledger records a March 2026 predecessor certification cycle. Its open items are historical and must not be interpreted as the current Crown-CSMS blocker register or investor-readiness state.


Status date: 2026-03-15
Current branch: fix/track11-12-write-and-lifecycle-proof
Current head sha: 34ca98d3
Current RC artifact: missing at frontend/dashboards/dist/release-candidate.json

## Bucket definitions

- Bucket 1: blocker to merge current branch
- Bucket 2: blocker to module completion
- Bucket 3: blocker to production certification
- Bucket 4: blocker to investor readiness

## Active blockers

| ID | Bucket | Blocker class | Owner | Current evidence | Exit criteria | Status |
|---|---|---|---|---|---|---|
| B1-001 | 1 | Proof job | TBD | PR 577 check gradebook-proof failed: https://github.com/tcmegahan/Crown2026/actions/runs/23114407819/job/67137361803 | gradebook-proof green for current head sha in PR checks | Open |
| B1-002 | 1 | Proof job | TBD | PR 577 check Proof Smoke (Playwright) failed: https://github.com/tcmegahan/Crown2026/actions/runs/23114407828/job/67137361817 | Proof Smoke green for current head sha in PR checks | Open |
| B1-003 | 1 | Security or quality gate | TBD | PR 577 CodeQL check failed: https://github.com/tcmegahan/Crown2026/runs/67144725660 with 10 new alerts (2 high, 8 medium); open PR code-scanning alerts currently 33 | CodeQL aggregate check green for current head sha in PR checks and no blocker-level alerts attributed to this PR | Open |
| B2-001 | 2 | Acceptance governance | TBD | Module matrix has many Incomplete or Unproven entries in MODULE_ACCEPTANCE_MATRIX_14.md | every module has owner + full acceptance fields + signoff evidence | Open |
| B2-002 | 2 | Route contract | TBD | No single locked route contract file designated as canonical for proof and role landings | one locked route contract is published and referenced by tests and workflows | Open |
| B2-003 | 2 | UI contract | TBD | No single locked heading and visible-surface contract designated for proof gates | one locked UI surface contract is published and referenced by proof tests | Open |
| B2-004 | 2 | Demo auth contract | TBD | Multiple token paths and assumptions exist across workflows and tests | one hardened demo token contract with local and CI parity is published and used | Open |
| B3-001 | 3 | Release truth | TBD | RC artifact file missing locally: frontend/dashboards/dist/release-candidate.json | RC artifact exists and contains release sha and tag for candidate release | Open |
| B3-002 | 3 | Production certification checklist | TBD | Production checklist not yet completed for current-cycle release | all checklist items in PRODUCTION_CERTIFICATION_CHECKLIST.md are evidence-complete | Open |
| B3-003 | 3 | Truth ledger discipline | TBD | Current-cycle deployed truth tuple not recorded here (deployed sha, runtime build_sha, deploy tag) | ledger includes deployed tuple and verification timestamp | Open |
| B4-001 | 4 | Investor packet completeness | TBD | Investor packet skeleton exists but evidence fields are not fully populated | INVESTOR_EVIDENCE_PACKET.md complete with all required artifacts attached | Open |
| B4-002 | 4 | Demo script certification | TBD | Investor demo script is not currently tied to certified release tuple | scripted runbook is verified against certified release sha and evidence output | Open |
| B4-003 | 4 | Known limitations register | TBD | No single investor-facing known-limitations section tied to current release | limitations are explicitly documented and signed off in investor packet | Open |

## Rule

No new work should start unless it references one blocker ID from this ledger.
