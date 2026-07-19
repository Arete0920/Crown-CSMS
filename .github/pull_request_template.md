# CROWN PR — Active Lane Required

## Ownership and authority

- Product Owner: TC Megahan
- Repository Owner: @tcmegahan
- Technical direction and acceptance authority: TC Megahan
- Production authorization granted by this PR: no

## Human ownership and AI assistance

- Human owner:
- Evidence-backed contributors:
- AI assistance: none / limited / material — describe scope
- Human verification:
- Unverified attribution:

AI tools are implementation aids, not owners, authors, independent reviewers, approvers, or release authorities. Contributor credit must be supported by durable evidence.

## Active lane

- PR:
- Branch:
- Worktree:
- Base SHA:
- Head SHA:
- Goal:
- Evidence output path:
- Completion claim allowed: no
- Independent review required: yes

## Purpose

<!-- One sentence: what does this PR do? -->

## Scope and blast radius

**Allowed changed files or directories:**

-

**Forbidden files or directories:**

- Everything else

## AI-pattern remediation record

Complete this section when the PR addresses issue #1432 or an AI-pattern finding.

- Finding IDs:
- Baseline behavior:
- Behavior intentionally changed:
- Reference analysis:
- Replacement or deletion analysis:
- Remaining findings:

An AI-pattern finding is a maintainability, verification, or provenance indicator. It is not proof of authorship.

## Lane guard

- [ ] Active lane packet exists
- [ ] `scripts/guards/assert_active_lane.ps1 -Lane <path>` ran and passed, if applicable
- [ ] Worktree was clean before validation
- [ ] Final `git status --short` captured
- [ ] Changed files match allowed scope

## Proof policy gate

**If this PR touches any of these, Proof — Gradebook must run and pass:**

- `.github/workflows/proof-gradebook.yml`
- `frontend/dashboards/tests/**`
- `frontend/dashboards/src/**`
- `backend/gradebook/**`
- `backend/academics/**`
- `backend/core/management/commands/**`
- `backend/crown_api/**`

- [ ] Proof — Gradebook ran and passed, if required
  - Proof run link:

## Dashboard certification safety

- [ ] This PR does not claim dashboard certification unless the matrix row is independently reviewed and promoted to CERTIFIED.
- [ ] This PR does not use sample data as production proof.
- [ ] This PR does not ask the Product Owner to self-review or self-approve an independent-review requirement.

## Proof

Paste raw outputs, exact-head CI links, or artifact paths. Do not list commands that were not run as proof.

### Local

```bash
git status -sb
git diff --stat
python backend/manage.py check
```

### CI and validation

- pytest:
- frontend unit tests:
- frontend build:
- Spine Audit:
- Proof Ceremony:
- Secret Scan:
- CI — Tests and Checks:
- Exact verified head SHA:

## Remaining NOT DONE / NOT VERIFIED

-

## Rollback plan

<!-- One line: revert commit, revert PR, or another exact rollback action. -->