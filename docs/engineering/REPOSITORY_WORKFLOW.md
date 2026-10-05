# CROWN Repository Workflow

**Status:** Canonical engineering workflow  
**Objective:** keep repository work bounded, reviewable, current and fully closed before new work accumulates.

## Core rule

Use one branch and one pull request for each coherent, reversible outcome.

Before editing, record the base SHA, scope, validation plan, decision owner and rollback action.

Every non-trivial change must:

- be reviewable line by line;
- include appropriate tests;
- preserve tenant and permission boundaries;
- pass applicable CI, security, dependency, schema, build and route checks;
- record the exact head being evaluated;
- avoid unsupported release claims.

Authentication, RBAC, tenant isolation, migrations, deployment, dependencies and security-sensitive configuration require explicit scope and proportional verification.

Production readiness is determined only from the exact repository head and its current release evidence.

## Closure-first discipline

A pull request is not complete when code is written or when an earlier CI run is green. It is complete only when it is merged or explicitly closed, the resulting integration line is verified, and any dependent work has been reconciled.

Before opening new ordinary work:

1. inspect the current open pull-request queue;
2. merge any current, mergeable, terminal-green PR that is already ready;
3. repair any bounded blocker that can be completed safely;
4. refresh or explicitly close stale/superseded PRs;
5. verify the current `main` head after every merge;
6. only then open the next independent lane.

## Work-in-progress limit

Normal operation should keep no more than **three active non-automated pull requests** at once.

A temporary exception is permitted only when:

- the work is intentionally stacked and the dependency is documented;
- an urgent security or production incident requires an isolated lane; or
- a maintainer records why parallel execution reduces rather than increases integration risk.

Repository remediation should normally use **one active remediation PR at a time**.

Prepared follow-up branches may exist without open PRs when sequencing them avoids unnecessary CI fan-out.

## Exact-head authority

Historical green workflow runs are useful evidence but are not merge authority after the PR head or integration base changes.

Before merge:

- confirm the exact PR head;
- confirm the current base;
- confirm mergeability;
- require applicable exact-head checks to be terminal-green;
- reject cancelled, superseded or stale runs as merge authority.

After merge, re-read `main` before certifying or refreshing the next PR.

## Stale and superseded work

Do not leave obsolete work presented as active.

When a PR is superseded:

- preserve any unique work that remains required;
- identify the replacement branch/PR when one exists;
- close the old PR explicitly;
- do not merge it merely to reduce the open count;
- do not rewrite history solely to improve appearance.

Stale feature work must be refreshed against the current integration line before certification.

## CI-load discipline

Do not create multiple branch refreshes simply to make all PRs appear current at once.

Prefer serial refresh and certification when each update triggers a broad CI matrix. This keeps evidence attributable, avoids Actions congestion and reduces false signal from stale heads.

Workflow architecture should follow `docs/engineering/CI_ARCHITECTURE.md`: stable terminal gate families, cancellation of superseded PR executions where safe, and retirement of one-time workflows after evidence is retained.

## Definition of done

For repository work, “done” means:

1. implementation complete;
2. focused validation complete;
3. exact-head required checks terminal-green;
4. PR merged or explicitly closed;
5. resulting `main` verified;
6. dependent PRs reassessed;
7. stale/superseded work removed from the active queue;
8. limitations or unverified deployment claims stated accurately.
