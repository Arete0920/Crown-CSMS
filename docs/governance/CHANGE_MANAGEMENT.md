# CROWN Change Management Policy

## Authority

Crown-CSMS changes are governed by its exact repository head, `docs/CURRENT_RELEASE_STATUS.md`, this policy, and the canonical index. Crown2026 issue #1619 is predecessor evidence only.

## Core rule

Create one pull request per coherent, independently reversible outcome. Before editing, record the exact base SHA, outcome, allowed and forbidden paths, validation, human decision owner, rollback, and facts not verified.

## Pull-request requirements

- Keep same-outcome implementation, tests, documentation, workflows, and review corrections together.
- Separate materially different security, privacy, legal, schema, deployment, dependency, credential, or rollback boundaries.
- Identify the final exact head and terminal applicable checks.
- Distinguish repository proof from deployed-runtime proof.
- Do not represent self-review, CI results, static analysis, or test results as independent human approval.
- Do not use historical branches, issues, PRs, or workflow runs as current authority.
- Do not close or discard work until unique content and acceptance criteria are dispositioned.

## Completion

A pull request is complete only when its final diff represents the coherent outcome, applicable checks pass on the exact head, actionable findings are resolved or explicitly dispositioned, rollback is stated, evidence limits are disclosed, and the authorized human decision is recorded.

Legal, tax, accounting, transaction, valuation, contractual, insurance, and payment-provider conclusions remain subject to qualified review.
