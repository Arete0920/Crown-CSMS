# CROWN Repository Agent Instructions

These instructions apply to repository-aware automation and coding assistants. Follow the current authoritative policies, not conversational recollections.

## Authority
- Repository: `Arete0920/Crown-CSMS`. Check the exact current branch/commit before consequential claims.
- Read `docs/governance/CROSS_CONVERSATION_CONTEXT.md`, `docs/engineering/REPOSITORY_WORKFLOW.md`, `docs/engineering/ENGINEERING_ACCOUNTABILITY_POLICY.md`, and relevant domain-specific canonical documents.
- This file is an execution aid, not a bypass of owner approval, protected branches, review, security, privacy, tenant isolation, testing, or release controls.

## Execute with evidence
1. Define the requested outcome and its acceptance evidence. Inspect the smallest relevant current source and state before editing.
2. Prefer the smallest coherent, reversible correction. Fix root causes; do not create status-only work, duplicate issues, or speculative remediation.
3. Implement and run relevant tests. On failure, investigate the diagnostic output, make a different evidence-supported repair, and rerun affected checks.
4. Use the existing branch/PR governance path; verify required exact-head checks and approval before merging. Deployment requires separately verified runtime/source identity and applicable operational tests.
5. Mark each distinct stage accurately: PROPOSED, IMPLEMENTED, TESTED, MERGED, DEPLOYED, VERIFIED COMPLETE, BLOCKED, or NOT VERIFIED. Do not collapse these into a generic "done".
6. When waiting on external CI or approvals, work on independently actionable tasks if tools and session time permit. Avoid repeated polling of unchanged state.
7. When blocked by a missing operation, permission, or external dependency, check for an authorized alternative once; never imply unavailable access or claim an attempted action succeeded.
8. Prioritize verified outcomes per tool call: batch independent reads, avoid redundant investigations, reuse valid exact-revision evidence, and keep output concise.
9. End with concrete changes (file paths, PRs, commit SHA, test/workflow evidence), actual completion state, and precisely scoped remaining blockers. Do not promise unattended work after the session ends.

## Non-negotiable truthfulness
- Prior chats, summaries, memory, speculative explanations, and green unrelated workflows are not proof of current implementation or deployment.
- Never fabricate actions, test results, approvals, source revisions, merges, deployments, or closure.
- If evidence is absent, say NOT VERIFIED; if an action is unavailable, say BLOCKED with the exact cause.
- Never weaken checks or conceal failures to produce a passing result.

## Operating boundary
Assistants cannot guarantee continuous execution through conversations. Recurrent work requires separately configured automation and credentials, plus the same governance controls. This file instructs behavior but cannot itself cause jobs to run.
