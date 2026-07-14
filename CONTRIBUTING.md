# Contributing to CROWN

## Purpose

This repository uses a controlled, proof-first contribution model.

`tcmegahan/Crown2026` is the sole active and authoritative repository. The former `Crown-Christian` repository has been permanently deleted.

Every change must be tightly scoped, reviewable, and supported by raw proof.

## Contribution model

This is a private, controlled contribution repository. Unsolicited or out-of-scope pull requests may be declined when they modify architecture without approval, exceed the stated scope, or lack supporting evidence.

## Ground rules

1. No unrelated refactors in the same pull request.
2. No generated artifacts unless explicitly required.
3. No secrets, credentials, or copied production data.
4. No public disclosure of vulnerabilities or sensitive findings.

## Branching

- Do not push directly to `main`.
- Use one branch per logical change.
- Keep branch names explicit: `feat/*`, `fix/*`, `chore/*`, `docs/*`, `security/*`.

## Pull-request requirements

Each pull request should include:

- one-sentence purpose;
- explicit scope and blast radius;
- raw local proof;
- raw CI proof;
- rollback plan where applicable;
- independent-review status.

Use `.github/pull_request_template.md` as the pull-request structure.

## Minimum local proof

```bash
git status -sb
git diff --stat
python backend/manage.py check
```

## Scope discipline

A pull request should modify only files needed for the stated purpose. Split unrelated work into separate pull requests.

## Root-file policy

Keep the repository root curated. Do not add one-off notes, proof dumps, or ad hoc summaries at root unless they are canonical.

Place material in the appropriate subtree instead:

- `docs/architecture/`;
- `docs/operations/`;
- `docs/security/`;
- `docs/evidence/`;
- `docs/investor/`;
- `scripts/`;
- `tools/`.

## Commit guidance

Use clear, scoped messages such as `feat: ...`, `fix: ...`, `chore: ...`, `docs: ...`, or `security: ...`.

## Security

Do not report vulnerabilities in public issues or pull-request comments. Follow `SECURITY.md` for all security-related reporting.

## Licensing and proprietary status

Unless a separate license file states otherwise, this repository is proprietary. Contributing code does not grant ownership or usage rights beyond terms explicitly accepted by the repository owner.

## Attribution and contributor records

Repository account attribution is not a complete contributor record. Contributor names, usernames, roles, and responsibility areas must be verified with the individuals involved before being added to handoff documentation or ownership controls.

## Questions

For contribution questions, contact the repository maintainer through the approved maintainer channel documented in `README.md`.
