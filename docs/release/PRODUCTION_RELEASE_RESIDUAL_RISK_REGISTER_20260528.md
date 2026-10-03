# Production Release Residual Risk Register - 2026-05-28

## Residual Risks

| Risk | Severity | Current Status | Mitigation | Proof Required to Close |
| --- | --- | --- | --- | --- |
| Scheduling module is draft/unreleased | High | Explicitly excluded from the approved release claim | Keep scheduling out of production release language until merged and gate-proven | Merge to main, run the required tests, and capture hosted/runtime gate proof |
| Live Azure smoke not freshly rerun in this review | Medium | No fresh live Azure smoke was performed in this review pass | Treat live runtime claims as bounded to existing evidence until rerun | Fresh live Azure smoke output showing the current approved slice is green |
| Billing recently had tenant authorization fixture correction | Medium | Billing is stable in the release slice, but fixture correction history requires continued regression attention | Keep billing golden path in release smoke coverage | Green billing golden-path tests and evidence on the current mainline |
| SOLOMON foundation is strong but not production-ingested | High | Structured foundation exists, but ingestion/content activation is not approved for production claims | Keep SOLOMON ingestion out of release scope | Explicit proof that ingestion is merged, tested, and gate-proven |
| Publisher resource work is metadata-only | Medium | Publisher-related work remains metadata/index-only | Do not treat metadata/index work as production content activation | Proof that publisher content workflows are merged and hosted-green |
| Unapproved automated decision support | High | Automated decision support is not approved as a client-facing production capability | Keep unapproved capabilities out of production claims | Gate proof that any client-facing decision-support surface is merged and approved |
| Release scope could be overstated if future modules are mentioned | High | Scope drift is possible if draft work is described as production-ready | Use the canonical scope lock and exclusion list in all release claims | No contradictory language in release docs plus canonical authority sync |
