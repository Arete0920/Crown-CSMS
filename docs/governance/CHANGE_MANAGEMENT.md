# CROWN Change Management Policy

## Purpose

CROWN uses pull requests to create reviewable, reversible, and evidence-backed changes. Pull requests must be organized around coherent outcomes rather than individual files, test cases, scanner findings, or workflow attempts.

The controlling production-readiness and owner-handoff structure remains GitHub issue #1619. This policy governs how implementation work is grouped and reviewed under that structure; it does not create a parallel plan or authority.

## Core rule

Create one pull request per coherent, independently reversible outcome.

A pull request should normally contain all implementation, tests, documentation, workflow adjustments, and review corrections required to complete that outcome. Defects discovered while validating the pull request stay in the same pull request unless they cross an independent risk or rollback boundary.

## Default operating model

- Maintain one active implementation pull request per workstream.
- Prefer one active implementation pull request across the repository when work is sequential.
- Group changes that share the same issue, subsystem, risk boundary, rollback plan, and acceptance campaign.
- Keep review corrections and exact-head validation repairs in the existing pull request.
- Use commits inside the pull request to preserve the implementation history instead of opening follow-up pull requests for each correction.
- Close obsolete drafts promptly and record whether they were superseded, diagnostic-only, or intentionally not merged.
- Do not use pull requests solely to trigger an audit or evidence run when an existing persistent workflow can be dispatched.

## Separate pull request criteria

A separate pull request is appropriate when at least one of the following is true:

1. The change has a materially different rollback boundary.
2. The change affects an independently governed security, privacy, legal, schema, deployment, dependency, or credential-control surface.
3. The change is unrelated product behavior and cannot be reviewed as part of the same outcome.
4. The current branch is no longer trustworthy because its history contains prohibited material or an immutable source boundary has become invalid.
5. Repository policy requires an isolated proof or approval path.

A separate pull request is not justified only because:

- another file needs correction;
- a test or scanner found a defect in the same outcome;
- a workflow needs a syntax or policy repair;
- evidence needs to be regenerated for the current head;
- the implementation spans frontend, backend, tests, and documentation for the same behavior;
- a change is small.

## Audit and evidence work

Audit and evidence activity should use persistent `workflow_dispatch` workflows whenever practical. Temporary audit branches or non-merge pull requests require a documented reason explaining why the evidence could not be produced from a persistent workflow or the current implementation pull request.

Evidence must identify the exact commit SHA it validates. A new commit invalidates prior exact-head evidence and requires the applicable checks to run again; it does not normally require a new pull request.

## Pull request preparation

Before opening a pull request, confirm:

- the intended outcome and controlling issue;
- whether an existing open pull request already covers the outcome;
- the allowed scope and rollback boundary;
- the validation campaign required for the final exact head;
- why a separate pull request is necessary if related work is already open.

## Pull request completion

A pull request is complete only when:

- its final diff represents the entire coherent outcome;
- applicable tests and policy checks pass on the exact head;
- review findings are resolved in the same pull request;
- superseded approaches are removed from the final diff;
- the rollback action is explicit;
- the description distinguishes repository proof from deployed production proof;
- no self-approval is represented as independent review.

## Owner and diligence review

Repository reviewers should evaluate the current operating model, authoritative status, final merged outcomes, and exact-SHA evidence. Historical diagnostic, superseded, or narrowly scoped pull requests remain part of the immutable engineering record but are not separate active authorities.

The repository should present:

- one authoritative current status;
- one controlling readiness and handoff structure;
- a small and clearly bounded active pull-request set;
- outcome-based change history;
- explicit disposition for unmerged work;
- persistent verification workflows rather than disposable trigger pull requests.

## Exceptions

Any exception must be stated in the pull request description with:

- the reason the work cannot remain in an existing pull request;
- the independent risk or rollback boundary;
- the controlling issue;
- the expected disposition of related branches and pull requests.
