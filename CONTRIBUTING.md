# Contributing to Crown2026

## Purpose

This repository uses a controlled, proof-first contribution model.

Repository lineage: Crown2026 is the current active platform repository. Crown-Christian is retained as an archived legacy repository.

Every change must be:

- tightly scoped
- easy to review
- supported by raw proof
- reversible
- limited to the explicit blast radius of the work

## Contribution posture

This is not a free-form public contribution repository.

Unsolicited pull requests may be declined if they:

- change behavior outside the agreed scope
- modify architecture without prior approval
- lack proof
- introduce generated debris or root clutter
- bypass security, operational, or release discipline

## Ground rules

1. No wandering.
2. No drive-by cleanup outside the approved scope.
3. No unrelated refactors in the same PR.
4. No generated artifacts committed unless explicitly required and documented.
5. No secret material, tokens, credentials, or copied production data in commits, issues, or PRs.
6. No public disclosure of vulnerabilities or sensitive operational findings.

## Canonical entrypoints

The canonical Django management entrypoint is:

```bash
python backend/manage.py <command>
```

Examples:

```bash
python backend/manage.py check
python backend/manage.py migrate
python backend/manage.py test
```

Use `backend/manage.py` consistently in scripts, documentation, and local validation.

## Branching model

- Do not push directly to `main`.
- Create a feature or fix branch for every change.
- Keep branches focused on one logical unit of work.
- Rebase or merge from `main` as needed to stay current if required checks enforce up-to-date branches.

Recommended branch naming:

- `feat/<short-scope>`
- `fix/<short-scope>`
- `chore/<short-scope>`
- `docs/<short-scope>`
- `security/<short-scope>`

Examples:

- `fix/codeql-blocking`
- `docs/root-readme`
- `chore/root-cleanup`
- `security/dependency-audit`

## Pull request standard

Every PR must include:

- one-sentence purpose
- explicit scope and blast radius
- exact list of allowed changed files or directories
- raw local proof
- raw CI proof
- rollback plan

Use `.github/pull_request_template.md` as the controlling PR shape.

## Required proof

At minimum, include raw output for:

```bash
git status -sb
git diff --stat
python backend/manage.py check
```

If your change affects frontend dashboards, gradebook, academics, core management commands, or API surfaces, include the relevant workflow and test proof required by the PR template.

Do not substitute summary language for proof.

Unacceptable:

- tested locally
- works on my machine
- CI looked good

Acceptable:

- raw command output
- exact workflow results
- direct proof links when manual workflow execution was required

## Scope discipline

A PR should modify only the files needed for the stated purpose.

If a file is outside the approved blast radius, do not touch it in the same PR.

If additional work is needed:

- open a separate issue
- or prepare a separate PR

## Root file policy

The repository root must remain curated.

Do not add one-off notes, proof dumps, reports, or ad hoc summaries to the root unless they are clearly canonical.

Place material in the appropriate subtree instead:

- `docs/architecture/`
- `docs/operations/`
- `docs/security/`
- `docs/evidence/`
- `docs/investor/`
- `scripts/`
- `tools/`

## Local development checklist

Before opening a PR:

```bash
git status -sb
git diff --stat
python backend/manage.py check
```

Then run the smallest relevant test set for the changed area.

Examples:

- backend changes: targeted Django tests
- frontend changes: package tests and relevant UI checks
- workflow changes: validate syntax and trigger behavior where appropriate
- deploy changes: include determinism and health proof if applicable

## Commit guidance

Use clear, scoped commit messages.

Preferred style:

- `feat: add X`
- `fix: correct Y`
- `chore: remove Z`
- `docs: clarify A`
- `security: enforce B`

Avoid vague messages like:

- updates
- fixes
- cleanup
- misc

## Review expectations

Reviewers may reject a PR for any of the following:

- unclear purpose
- oversized blast radius
- inadequate proof
- security concerns
- operational risk
- missing rollback path
- root clutter
- undocumented new behavior

## Security

Do not report vulnerabilities in public issues or public PR comments.

Follow `SECURITY.md` for all security-related reporting.

## Licensing and proprietary status

Unless a separate license file states otherwise, this repository is proprietary.

Contributing code does not grant you any ownership or usage rights beyond the terms explicitly accepted by the repository owner.

## Questions

For contribution questions, contact the repository maintainer through the preferred maintainer channel documented in `README.md`.
