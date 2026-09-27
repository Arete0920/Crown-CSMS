# Release authority truth repair

Base: `b0a537fc6ce3bcb26eb6b007b43088bd3da1e2e1` (`main` at scope definition).

Outcome: state that the August certification is historical, keep a successor production identity unasserted, and align freshness/frontend contracts with those facts.

Allowed files: `docs/CURRENT_RELEASE_STATUS.md`, `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`, `frontend/dashboards/src/tests/releaseAuthorityConsistencyContract.test.js`, `frontend/dashboards/src/tests/buyerWalkthroughContract.test.js`, and this record.

Forbidden: modifying freshness-gate logic or thresholds, fabricating deployment identity, changing authentication, migrations, or branch rules.

Validation: repository freshness checker, focused Vitest contracts, normal PR hygiene, and exact-head GitHub checks. Deployment identity and full release readiness remain NOT VERIFIED.

Decision owner: repository owner. Rollback: revert this PR only after replacing the release claim with equally current verified evidence; never restore an unsupported production-ready assertion. Automated checks are not independent human approval.
