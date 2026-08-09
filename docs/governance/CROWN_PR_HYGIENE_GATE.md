# CROWN PR Hygiene Gate

Status: Governance control document  
Scope: Pull requests, generated evidence, dashboard certification evidence, release-readiness evidence, and solo-developer control-path language

## 1. Purpose

CROWN pull requests must remain clean, reviewable, reproducible, and evidence-first.

Generated audit noise, stale evidence dumps, oversized diffs, and invalid review-wait language are not acceptable merge conditions.

This policy makes PR hygiene a required control before release, sandbox, pilot, production, dashboard certification, wizard certification, or module-certification decisions.

## 2. Mandatory Rule

A PR is NO-GO when any of these are true:

- changed-file count exceeds the defined hygiene threshold without an explicit architectural exception,
- added lines exceed the defined hygiene threshold,
- bulky generated JSON, Markdown, logs, traces, screenshots, or local audit dumps are committed instead of uploaded as workflow artifacts,
- timestamped stale evidence folders are committed as durable source truth,
- PR body waits for an unavailable independent human reviewer instead of using the approved solo-developer workaround,
- PR body makes release, sandbox, pilot, production, or certification claims without current evidence tied to the PR head SHA.

## 3. Commit vs Artifact Rule

Commit to the repository:

- source scripts,
- schemas,
- compact human-readable summaries,
- canonical product/configuration state,
- durable governance documents.

Do not commit to the repository by default:

- bulky generated JSON,
- bulky generated Markdown,
- raw inventory dumps,
- local browser traces,
- screenshots,
- transient audit outputs,
- timestamped stale evidence folders,
- logs.

Store bulky generated proof as GitHub Actions artifacts with retention instead of committing it to the PR branch.

## 4. Default Thresholds

| Gate | Default limit |
| --- | ---: |
| Normal PR additions | 1,500 |
| Documentation/audit PR additions | 3,000 |
| Changed files | 20 |
| Generated audit JSON in `audit-artifacts/` | blocked by default |
| Timestamped evidence folders | blocked by default |

Exceptions must be explicit in the PR body and must be supported by a current evidence packet.

## 5. Solo-Developer Review Language

CROWN does not wait for a nonexistent independent human reviewer.

When the product owner is the solo developer, use the approved solo-developer workaround:

```text
Segregation of duties:
The product owner is the solo developer and cannot self-review or self-approve this work.

Independent human reviewer:
Unavailable for this solo-developer operating model.

Control path used:
Solo-developer approved workaround using GitHub connector evidence, GitHub required checks, CI/release gates, PR diff review, and explicit PASS / NO-GO evidence packet.

Development-support role:
Support, architecture, engineering review, and evidence audit only. Automated assistance is not approval authority.
```

## 6. Required Enforcement

The `PR Hygiene Gate` workflow must run on pull requests.

The check should be treated as required for merge once repository rulesets are updated.

Until it is required by ruleset, any PR failing this gate remains draft, blocked, or NO-GO.

## 7. Dashboard-Specific Rule

Dashboard certification PRs must not commit generated certification truth dumps as durable source truth.

Dashboard certification work should remain in one coherent, independently reversible pull request containing the implementation, evidence-generation scripts, compact evidence summary, denominator/state reconciliation, and certification promotion required for the same outcome. A separate pull request requires an independent risk, authority, or rollback boundary under `docs/governance/CHANGE_MANAGEMENT.md`.

A dashboard is not certified until route, permission, tenant, runtime/browser, evidence packet, state/matrix, and solo-developer workaround record all agree.
