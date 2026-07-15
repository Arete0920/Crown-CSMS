# Contributing to Crown2026

## Purpose

This repository uses a controlled, proof-first contribution model.

Repository lineage: `tcmegahan/Crown2026` is the sole active and authoritative CROWN repository. The former `tcmegahan/Crown-Christian` repository has been permanently deleted and is not an authority source.

Every change must be tightly scoped, reviewable, and supported by raw proof.

## Contribution Model

This is not a free-form public contribution repository. Unsolicited pull requests may be declined when they exceed scope, modify architecture without approval, or lack proof.

## Ground Rules

1. No unrelated refactors in the same PR.
2. No generated artifacts unless explicitly required.
3. No secrets, credentials, or copied production data.
4. No public disclosure of vulnerabilities or sensitive findings.

## Branching

- Do not push directly to `main`.
- Use one branch per logical change.
- Keep branch names explicit: `feat/*`, `fix/*`, `chore/*`, `docs/*`, `security/*`.

## Pull Request Requirements

Each PR should include:

- one-sentence purpose
- explicit scope and blast radius
- raw local proof
- raw CI proof
- rollback plan

Proof must match the change scope. Documentation-only PRs must not be represented as runtime certification and should not invoke runtime proof ceremonies.

Use `.github/pull_request_template.md` as the PR shape.

## Minimum Local Proof

```bash
git status -sb
git diff --stat
python backend/manage.py check
```

## Scope discipline

A PR should modify only files needed for the stated purpose. If more work is needed, split it into a separate PR.

## Root file policy

Keep the repository root curated. Do not add one-off notes, proof dumps, or ad hoc summaries at root unless canonical.

Place material in the appropriate subtree instead:

- `docs/architecture/`
- `docs/operations/`
- `docs/security/`
- `docs/evidence/`
- `docs/investor/`
- `scripts/`
- `tools/`

## Commit guidance

Use clear, scoped messages such as `feat: ...`, `fix: ...`, `chore: ...`, `docs: ...`, `security: ...`.

## Security

Do not report vulnerabilities in public issues or public PR comments.

Follow `SECURITY.md` for all security-related reporting.

## Licensing and proprietary status

Unless a separate license file states otherwise, this repository is proprietary.

Contributing code does not grant you any ownership or usage rights beyond the terms explicitly accepted by the repository owner.

## Questions

For contribution questions, contact the repository maintainer through the preferred maintainer channel documented in `README.md`.
