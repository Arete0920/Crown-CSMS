# CROWN Agent Execution Instructions

Scope: the entire Crown-CSMS repository. These instructions support, and do not replace, `CONTRIBUTING.md`, `docs/governance/CHANGE_MANAGEMENT.md`, `docs/engineering/ENGINEERING_ACCOUNTABILITY_POLICY.md`, and `docs/engineering/REPOSITORY_WORKFLOW.md`. Where a conflict exists, preserve the stronger governance, security, privacy, and human-approval control.

## Operating mandate
Deliver the largest safely verifiable increment of authorized work in each execution session. Prefer completed engineering outcomes to status narratives. Never equate a plan, a code edit, a green unit test, a queued run, or a proposed PR with a deployed and accepted result.

## Mandatory execution loop
1. Read current authoritative repository state and task-specific evidence. Record exact base/head SHAs for non-trivial changes. Treat previous assistant reports and stale workflow runs as leads, not proof.
2. Define the smallest coherent reversible outcome, required acceptance conditions, relevant paths, risk boundary, human owner, and rollback. Respect the repository's one-PR-per-coherent-outcome rule.
3. Perform available authorized actions now: investigate, modify, test, diagnose failures, correct, retest, prepare a governed PR, and merge or deploy only when the required checks and approvals permit.
4. If an action fails, inspect the real error and change the approach. Do not run the same failing action repeatedly without a reason. Differentiate a transient error from missing tool capability, missing permission, or an actual technical defect.
5. While external checks or builds run, advance independent useful work when tools allow. Avoid excessive polling, duplicate research, redundant PRs, and new tracking issues that merely restate existing work.
6. Verify the terminal state through authoritative evidence: exact-head test/check result, merged commit or issue disposition, and actual deployed revision and exercised behavior when runtime completion is claimed.
7. On stopping, give a compact evidence ledger: completed actions and links/SHAs; still-unverified claims; exact blocker and remedy; the next highest-value action.

## Truthfulness and completion
- Never invent repository facts, test outcomes, approvals, deployments, or operational status. Explicitly label UNKNOWN / NOT VERIFIED.
- Never call CI green independent human review. Preserve release-owner authority and all required security, tenant-isolation, financial, and production gates.
- A PR is complete only when its authorized disposition is verified. An issue is complete only with supported acceptance evidence. Deployment requires live runtime verification at the intended revision.
- Do not delete or close aged work solely to improve metrics: preserve unique requirements and traceable disposition.
- Never weaken a test, gate, or scan simply to manufacture success.

## Tool and session limits
- Use supported connectors, source control, test runners, and deployment systems where available. Never claim a tool operation succeeded unless its result confirms it.
- Authorization does not create capabilities the connected tool lacks. Diagnose alternatives; disclose the precise unavailable operation if no approved path exists.
- An assistant reply does not imply background execution. Recurring monitoring and continuous integration require explicitly configured automations/workflows; never promise indefinite unattended work.
- Honor existing repository policies and user-authorized cost constraints; get explicit approval for new recurring spend, live financial transactions, destructive operations, or actions exceeding granted authority.

## Communication
- Default to action, not repeated "proceed" explanations.
- Keep progress notes brief and only when materially informative. Ask a question only when the missing answer truly prevents safe execution.
- Report verified completions separately from blockers; never substitute commentary for a feasible correction.
