# CROWN Team Collaboration Operating Model

## Purpose

This document defines how CROWN collaborators coordinate work, make decisions, review changes, preserve evidence, and hand work to one another.

GitHub is the system of record for repository work. Meetings, email, text, and private chat may support discussion, but decisions and assignments that affect CROWN must be summarized in the relevant GitHub issue, pull request, or architecture decision record.

## Roles

### Founder and Product Owner

John T. C. Megahan is the creator of CROWN, Founder, Product Owner, principal product designer, architecture and workflow authority, repository owner, technical direction authority, acceptance authority, and final release authority.

### Collaborators

Early, interim, and later collaborators may support bounded work under the Founder/Product Owner's direction. Active documentation does not enumerate individuals unless identification is operationally, legally, or evidentially necessary. Specific contribution credit must remain evidence-based.

### New collaborators and reviewers

Johnny Megahan and Evan Lesage are new collaborators and human reviewers. They must not be assigned historical implementation credit for work completed before their involvement.

## Access model

Access is granted only to verified GitHub usernames.

Recommended default permissions:

- **Read:** orientation or audit-only access.
- **Triage:** issue and pull-request coordination without code push rights.
- **Write:** normal branch, commit, and pull-request work.
- **Maintain:** workflow, release, and repository-management responsibilities without full administrative control.
- **Admin:** limited to repository ownership, emergency administration, and approved backup administration.

Use the least privilege necessary. Do not grant administrator access merely to make onboarding easier.

## Work ownership

Every material change requires:

1. one owning issue;
2. one logical branch;
3. one accountable owner;
4. defined scope and excluded scope;
5. expected validation evidence;
6. a rollback or reversal method.

A collaborator claims work by commenting on the owning issue with:

- name;
- branch;
- intended files or domain;
- expected proof;
- known dependencies;
- expected handoff point.

## Branching

Use one branch per logical change.

Preferred branch names:

- `feat/<description>`
- `fix/<description>`
- `docs/<description>`
- `security/<description>`
- `chore/<description>`

Do not push directly to `main`.

## Pull requests

Open draft pull requests early for visibility.

Each pull request must identify:

- purpose;
- exact scope;
- architectural impact;
- security, tenant, and data risks;
- validation performed;
- evidence locations;
- remaining limitations;
- rollback plan;
- Product Owner and review requirements.

Keep runtime, deployment, workflow, security, schema, governance, tests, and documentation for the same coherent outcome in one pull request. Separate them only when they have an independent risk, authority, or rollback boundary under `docs/governance/CHANGE_MANAGEMENT.md`.

## Review

Review must address correctness, architecture, security, tenant isolation, data integrity, operability, and maintainability where applicable.

Review comments must be resolved through one of the following:

- code or documentation change;
- new evidence;
- explicit rejection with rationale;
- documented deferral to a new issue with owner and acceptance criteria.

A resolved conversation is not automatically an approved change.

Independent review may not be satisfied by the person who authored or directed the change when independence is explicitly required.

## Architecture decisions

Material architecture choices require an Architecture Decision Record before or with implementation.

An ADR must document:

- context;
- decision;
- alternatives considered;
- consequences;
- migration or adoption plan;
- rollback or reversal considerations;
- security, tenant, and data implications;
- approval and review status.

## Communication

### Start of work

Post a comment on the owning issue before implementation begins.

### Material finding

Record material findings immediately on the issue or pull request. Do not wait for a meeting or weekly summary.

### Blocker

A blocker report must state:

- what is blocked;
- evidence;
- owner;
- decision or resource required;
- downstream impact.

### Handoff

A handoff must include:

- current branch and commit;
- files changed;
- commands or checks run;
- passed and failed evidence;
- unresolved risks;
- exact next action.

### Weekly coordination

The team collaboration hub issue should be updated with:

- active owners;
- active pull requests;
- blocked work;
- stale work;
- decisions required;
- merged outcomes;
- upcoming review needs.

## Work-in-progress limits

Maintain one active implementation pull request per workstream and prefer one active implementation pull request across the repository when work is sequential. Additional simultaneous work requires an independent risk or rollback boundary plus a written dependency and conflict assessment.

## Evidence policy

Completion claims require evidence tied to the exact commit under review.

Evidence should identify:

- repository and branch;
- commit SHA;
- environment;
- command or workflow;
- date and time;
- result;
- artifact or log location.

Screenshots and narrative summaries do not replace raw logs, test results, network evidence, or migration reconciliation where those are required.

## Release authority

Implementation approval, merge approval, sandbox authorization, pilot authorization, and production authorization are separate decisions.

No collaborator, automated workflow, development-support service, or tool independently grants production authorization. Production authorization requires an explicit Product Owner decision after applicable evidence gates pass.

## Onboarding checklist

Each collaborator should complete:

- repository access confirmed;
- clean clone completed;
- local environment created;
- backend check completed;
- relevant frontend build completed;
- test command completed;
- branch and draft pull request created;
- review submitted on a non-production change;
- architecture and release documents read;
- security and data-handling rules acknowledged;
- assigned domain and backup reviewer recorded.

## Offboarding and access review

When a collaborator changes role or leaves the project:

- revoke or reduce repository access;
- remove stale credentials and tokens;
- rotate shared or exposed secrets;
- transfer open issues and pull requests;
- update CODEOWNERS and ownership records;
- preserve contribution history;
- document the access-review result.