# Contributing to CROWN

## Purpose

This repository uses a controlled, proof-first contribution model.

Repository lineage: `tcmegahan/Crown2026` is the sole active and authoritative CROWN repository. The former `tcmegahan/Crown-Christian` repository has been permanently deleted and is not an authority source.

Every change must be tightly scoped, reviewable, and supported by current proof.

## Contribution model

This is not a free-form public contribution repository. Unsolicited pull requests may be declined when they exceed scope, modify architecture without approval, or lack proof.

## Ground rules

1. No unrelated refactors in the same PR.
2. No generated artifacts unless explicitly required.
3. No secrets, credentials, or copied production data.
4. No public disclosure of vulnerabilities or sensitive findings.
5. No retroactive or inferred contributor attribution without durable evidence.
6. No AI-generated summary, test, or review may be represented as independent human review.
7. No AI-pattern finding may be represented as proof of AI authorship.

## Human ownership, contributor evidence, and AI assistance

Follow:

- `docs/engineering/HUMAN_OWNERSHIP_AND_AI_ASSISTANCE_POLICY.md`;
- `docs/engineering/CONTRIBUTION_EVIDENCE_LEDGER.md`;
- `docs/engineering/AI_PATTERN_REFACTORING_STANDARD.md`.

TC Megahan remains Founder/Product Owner and the authority for requirements, technical direction, acceptance, and release authorization.

Anthony Rizzo, Ayush Agarwal, and Jed Hansen are founding/early collaborators. Credit specific work only when repository history or another retained record supports the attribution.

Johnny Megahan and Evan Lesage are new collaborators. Do not assign them historical contributions or prior work.

AI tools may assist with implementation, analysis, testing, documentation, and repository operations. The human owner remains accountable for scope, review, verification, security, and acceptance.

Each non-trivial pull request must disclose:

```text
Human owner: <name>
Evidence-backed contributors: <names or none>
AI assistance: <none | limited | material; describe scope>
Human verification: <review and validation actually performed>
Unverified attribution: <items or none>
```

## Branching

- Do not push directly to `main`.
- Use one branch per logical change.
- Keep branch names explicit: `feat/*`, `fix/*`, `chore/*`, `docs/*`, `security/*`, or `agent/*` for connector-managed scoped work.

## Pull request requirements

Each PR should include:

- one-sentence purpose;
- explicit scope and blast radius;
- raw local proof when local execution is available;
- raw CI proof at the exact PR head SHA;
- rollback plan;
- human ownership and AI-assistance disclosure;
- remaining `NOT VERIFIED` items.

Proof must match the change scope. Documentation-only PRs must not be represented as runtime certification and should not invoke runtime proof ceremonies.

Use `.github/pull_request_template.md` as the PR shape.

## Minimum local proof

```bash
git status -sb
git diff --stat
python backend/manage.py check
```

When local execution is unavailable, state that limitation and use exact-head CI or another current evidence source. Do not substitute an unrun command list for proof.

## Scope discipline

A PR should modify only files needed for the stated purpose. If more work is needed, split it into a separate PR.

Implementation refactors, governance documentation, CI changes, and release certification must remain separate unless explicit authority permits a combined change.

For AI-pattern remediation, use bounded subsystem-specific batches and follow `docs/engineering/AI_PATTERN_REFACTORING_STANDARD.md`.

## Root file policy

Keep the repository root curated. Do not add one-off notes, proof dumps, or ad hoc summaries at root unless canonical.

Place material in the appropriate subtree instead:

- `docs/architecture/`;
- `docs/operations/`;
- `docs/security/`;
- `docs/evidence/`;
- `docs/investor/`;
- `docs/engineering/`;
- `scripts/`;
- `tools/`.

## Commit guidance

Use clear, scoped messages such as `feat: ...`, `fix: ...`, `chore: ...`, `docs: ...`, or `security: ...`.

Commit authorship must reflect the authenticated human or service identity that created the commit. Do not rewrite history or add names merely to improve the appearance of individual contribution.

## Security

Do not report vulnerabilities in public issues or public PR comments.

Follow `SECURITY.md` for all security-related reporting.

## Licensing and proprietary status

Unless a separate license file states otherwise, this repository is proprietary.

Contributing code does not grant ownership or usage rights beyond the terms explicitly accepted by the repository owner.

## Questions

For contribution questions, contact the repository maintainer through the preferred maintainer channel documented in `README.md`.