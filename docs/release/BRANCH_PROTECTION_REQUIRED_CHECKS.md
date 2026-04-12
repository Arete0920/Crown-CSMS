# REQUIRED CHECKS ON `main`

Require pull request before merge.
Require at least 1 approval.
Require Code Owners review where available.
Dismiss stale approvals.
Require status checks to pass before merge.

Required check names:
- backend-gate
- frontend-gate
- contract-gate
- secret-scan
- CodeQL
- backend-pip-audit
- frontend-npm-audit
- release-verify

Block force pushes.
Block branch deletion.
Restrict direct pushes to main.
Disable admin bypass unless there is a written emergency exception.