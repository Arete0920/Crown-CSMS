# CROWN PR — Active Lane Required

## Ownership and authority

- Product Owner: TC Megahan
- Repository Owner: @tcmegahan
- Technical direction and acceptance authority: TC Megahan
- Production authorization granted by this PR: no

## Contributors and verification

- Human owner:
- Evidence-backed contributors:
- Implementation support:
- Human verification:
- Unverified attribution:

Contributor credit must be supported by durable evidence. Implementation support is not independent review, approval, certification authority, or release authority.

## Change-management classification

- [ ] This PR represents one coherent, independently reversible outcome.
- [ ] Related implementation, tests, documentation, workflow corrections, and review fixes are consolidated here.
- [ ] No existing open PR already covers this outcome.
- [ ] A separate PR is justified by an independent risk or rollback boundary, if related work exists.
- [ ] This PR is not being used only to trigger an audit or evidence run when a persistent workflow is available.

Policy: `docs/governance/CHANGE_MANAGEMENT.md`

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

<!-- One sentence: what coherent outcome does this PR complete? -->

## Scope and blast radius

**Allowed changed files or directories:**

-

**Forbidden files or directories:**

- Everything else

## Separate-PR justification

Complete this section when related work is already open or recently superseded.

- Existing related PR or branch:
- Independent risk or rollback boundary:
- Why the work cannot remain in the existing PR:
- Expected disposition of related work:

## Pattern-remediation record

Complete this section when the PR addresses issue #1432 or a generated-pattern finding.

- Finding IDs:
- Baseline behavior:
- Behavior intentionally changed:
- Reference analysis:
- Replacement or deletion analysis:
- Remaining findings:

A pattern finding is a maintainability, verification, or provenance indicator. It is not proof of authorship.

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
