# CROWN ChatGPT + GitHub Connector Protocol

Status: Governance control document  
Purpose: Minimize VS Code dependency and make ChatGPT plus GitHub connector the primary architecture, audit, and evidence workflow.

## 1. Core Principle

ChatGPT is the architecture, engineering, audit, and release-gate reasoning layer. GitHub connector is the repository evidence layer. GitHub Actions is the automated proof layer. Azure is the runtime layer.

VS Code is optional and should be used only when the proof cannot be obtained through GitHub, CI, artifacts, or Azure.

## 2. Required ChatGPT Behavior

For Crown2026 work, ChatGPT must:

1. Use GitHub connector first when current repository truth matters.
2. Separate verified facts from assumptions.
3. Avoid stale-memory claims.
4. Avoid declaring partial work complete.
5. Mark unverified items UNKNOWN.
6. Mark incomplete proof as NO-GO.
7. Preserve segregation of duties; do not ask the product owner to self-review their own work.
8. Prefer narrow, scoped branches and draft PRs for repository changes.
9. Avoid unrelated refactors.
10. Produce evidence-backed packets for meaningful decisions.

## 3. Standard GitHub Inspection Loop

For any audit, implementation, PR, or release question:

```text
1. Confirm repository.
2. Confirm default branch or target branch.
3. Confirm current branch/head SHA when relevant.
4. Inspect open PRs/issues when relevant.
5. Inspect changed files and diffs when relevant.
6. Inspect relevant source files directly from GitHub.
7. Inspect workflow/check status when relevant.
8. Inspect artifacts/logs when needed.
9. Produce verified facts, unknowns, risks, and next action.
```

## 4. Standard Prompt Mode

Use this mode for future Crown work:

```text
CROWN GITHUB-CONNECTOR MODE

Use GitHub connector as the primary source of repo truth.

Goal:
[insert goal]

Rules:
- Do not rely on VS Code unless unavoidable.
- Do not rely on memory as proof.
- Inspect current GitHub state first.
- Verify branch, PR, changed files, workflow/check status, and relevant source files.
- Separate verified facts from assumptions.
- Do not call work complete unless GitHub/CI/Azure/evidence proves it.
- If local execution is required, state exactly why and what proof is needed.

Return:
1. verified current state
2. relevant GitHub evidence inspected
3. risks
4. exact next engineering action
5. proof required for completion
```

## 5. Standard PR Review Mode

```text
CROWN PR REVIEW MODE

Review PR #[number] using GitHub connector.

Inspect:
- PR metadata
- head SHA
- base branch
- changed files
- full diff
- workflow status
- reviews/comments
- relevant surrounding source files if needed

Return:
- summary
- scope compliance
- risk findings
- test evidence
- missing proof
- approve/comment/request-changes recommendation

Do not approve on behalf of the product owner unless explicitly instructed and governance permits it.
```

## 6. Standard Release-Gate Mode

```text
CROWN RELEASE-GATE MODE

Evaluate release or deployment readiness using GitHub connector and available CI/Azure evidence.

Return:
1. PASS / NO-GO / BLOCKED
2. verified facts
3. missing proof
4. failed checks
5. risks
6. required next action
```

## 7. Connector Write Rules

Connector writes are allowed only when the change is narrow, reviewable, and safe.

Approved pattern:

1. Inspect file or target state first.
2. Create a new branch from the current base.
3. Make a narrow file change.
4. Open a draft PR.
5. Let checks run.
6. Review diff and checks.
7. Request independent review.

Do not use connector writes for broad refactors, generated bulk rewrites, destructive operations, secret changes, or production deployment bypasses.

## 8. Evidence Packet Requirement

Meaningful work must end with one of these packet types:

- Architecture Packet
- Engineering Packet
- Audit Packet
- PR Review Packet
- Release-Gate Packet
- Azure Deployment Packet
- Correction Packet

Each packet must identify:

- repository,
- branch,
- SHA,
- changed files when applicable,
- tests/checks reviewed,
- evidence sources,
- PASS/NO-GO/BLOCKED decision,
- next action.

## 9. Local Tool Escalation Rule

Use local/VS Code work only when one of these applies:

- CI cannot reproduce the issue,
- browser/UI proof is required,
- environment variables or secrets require a local authorized session,
- artifact inspection is too large for connector review,
- Azure behavior requires direct portal/runtime verification.

When local proof is used, it must be summarized and tied back to GitHub/Azure evidence whenever possible.
