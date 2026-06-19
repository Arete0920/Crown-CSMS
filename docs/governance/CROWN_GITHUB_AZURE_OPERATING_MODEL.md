# CROWN GitHub-to-Azure Operating Model

Status: Governance control document  
Scope: Crown2026 repository, pull requests, evidence gates, and Azure deployment path  
Primary rule: GitHub is the deployment truth source. Azure deploys only from verified GitHub state. VS Code is an optional local utility, not a release authority.

## 1. Operating Chain

The approved Crown engineering and deployment chain is:

```text
ChatGPT
  -> architecture, engineering guidance, audit, release-gate review
GitHub connector
  -> repo truth, branch truth, PR truth, workflow truth, artifact truth
GitHub Actions
  -> automated build, test, proof, and deployment gates
Azure
  -> staging and production runtime
```

VS Code is outside the primary chain. It may be used for local execution, but it must not be treated as a completion or deployment authority.

## 2. Source-of-Truth Rules

1. GitHub is the authoritative source for branch, commit, PR, diff, workflow, and artifact state.
2. Azure deployment must be tied to a specific GitHub commit SHA.
3. Local editor state is not proof.
4. Memory is not proof.
5. Screenshots are supporting evidence only; they do not replace repository, CI, or runtime proof.
6. Unknown items remain marked UNKNOWN until verified.

## 3. Default Crown Engineering Flow

For every non-trivial change:

1. Inspect current GitHub state.
2. Create or use a scoped branch.
3. Keep the change narrow and aligned to the stated goal.
4. Open a draft PR unless the work is explicitly documentation-only and already governed.
5. Let GitHub checks run.
6. Review changed files, workflow status, and artifacts.
7. Request independent review when governance requires it.
8. Merge only after required proof is green and review requirements are satisfied.
9. Deploy to Azure only through the approved GitHub workflow path.
10. Capture post-deploy evidence.

## 4. VS Code Minimization Rule

VS Code should be minimized for Crown governance, release readiness, and deployment decisions.

Use VS Code only when required for:

- local runtime reproduction,
- manual browser verification,
- local-only test execution,
- secret-bearing environment access that cannot be exposed in chat,
- complex generated artifact inspection.

If VS Code is used, its output must be converted into evidence and cross-checked against GitHub, CI, or Azure where possible.

## 5. Deployment Gates

### 5.1 Before Azure Staging Deployment

Required proof:

- repository confirmed,
- branch confirmed,
- HEAD SHA confirmed,
- PR/diff reviewed when applicable,
- backend checks pass when backend is affected,
- frontend build/tests pass when frontend is affected,
- migration risk reviewed when models/schema are affected,
- tenant/security implications reviewed when auth, roles, school isolation, or data access are affected,
- deployment workflow succeeds,
- Azure staging health check passes.

### 5.2 Before Azure Production Deployment

Required proof:

- staging deployment PASS,
- no failed required checks on the deployment SHA,
- no unresolved required reviews,
- no unknown migration state,
- no known tenant/security regression,
- release branch/tag confirmed if used,
- production deployment workflow succeeds,
- post-deploy smoke tests pass,
- rollback path identified.

## 6. Required Deployment Packet

Every Azure deployment must produce or reference a packet with this structure:

```text
CROWN AZURE DEPLOYMENT PACKET

Environment:
staging / production

Repository:
tcmegahan/Crown2026

Branch:
[name]

Commit SHA:
[sha]

PR:
[number / URL / not applicable]

Changed files:
[list]

Checks:
[PASS / FAIL / UNKNOWN]

Deployment workflow:
[name / run id]

Azure target:
[app / resource group / environment]

Post-deploy tests:
- health endpoint
- login/auth check if applicable
- API smoke check if applicable
- critical route check if applicable
- tenant isolation smoke check if applicable

Result:
PASS / NO-GO / ROLLBACK REQUIRED

Known risks:
[list or none]

Next action:
[exact next step]
```

## 7. PASS / NO-GO Rules

A release or deployment is PASS only when the required proof exists and matches the target SHA.

A release or deployment is NO-GO when any of these are true:

- required checks are failed,
- required checks are missing or stale,
- branch or SHA is ambiguous,
- required review is missing,
- migration state is unknown,
- tenant/security proof is missing for relevant changes,
- Azure health check fails,
- post-deploy smoke proof is missing,
- rollback path is unknown for production.

## 8. Independent Review Rule

The product owner cannot serve as independent reviewer for work they own or directed. Review and approval must be routed through an appropriate independent reviewer, required GitHub ruleset, or release authority.

ChatGPT may inspect, audit, draft, patch, and recommend. ChatGPT must not be treated as the independent human approval authority.

## 9. Crown Evidence Language

Use these terms consistently:

- VERIFIED: supported by current GitHub, CI, Azure, artifact, or directly supplied evidence.
- UNKNOWN: not proven by current evidence.
- BLOCKED: external dependency prevents forward progress.
- NO-GO: proof is incomplete, failing, stale, or unsafe.
- PASS: all required evidence is complete and green.

## 10. Implementation Standard

No Crown work is complete because a screen renders or a local command appeared successful. Work is complete only when the defined goal is proven against the required evidence path.

For module, dashboard, wizard, security, and deployment work, the default posture remains NO-GO until proof is complete.
