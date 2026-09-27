# Superseded PR validation cleanup

Base: b0a537fc6ce3bcb26eb6b007b43088bd3da1e2e1
Branch: ci/cancel-superseded-pr-runs
Decision owner: TC Megahan; workflow cleanup explicitly authorized.

Outcome: cancel obsolete executions when newer commits arrive on the same PR in CI - Tests and Checks, pytest-gate, dashboards-build-gate and Dependency Scan. The existing workflow/ref concurrency groups keep distinct PRs isolated. Push, scheduled and manual executions keep cancellation disabled.

Allowed scope: only concurrency.cancel-in-progress in those four workflows and this record. Triggers, jobs, steps, permissions, thresholds, security checks and deployment are unchanged. This resource-efficiency change is independently reversible from PR #12's startup-failure investigation. PR #12 had no changed files at preparation time; its branch was not modified.

Validation: all four original and updated YAML files parsed with PyYAML BaseLoader; structural comparison proved the sole semantic change is PR-only cancellation. Groups were checked for uniqueness and PR-ref separation. Existing tools/verify_workflow_policy.py passed for all four updated files. Hosted exact-head CI and runtime cancellation behavior remain NOT VERIFIED while job startup is blocked. No startup root cause is claimed.

Rollback: revert this commit. Superseded PR runs will again be allowed to finish. Merge only after applicable final-head checks and review; no production deployment is involved.
