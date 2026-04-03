# PR Triage Plan

This is a governance plan only. No PRs are closed automatically in Phase 1.

## Categories

### merge now

- Small, green, low-risk PRs with clear ownership and no overlapping files.
- Infra/doc-only PRs that reduce noise and do not affect runtime behavior.

### close stale

- PRs with no activity in the defined stale window and no owner response.
- PRs superseded by merged work where rebasing adds no value.

### superseded by later work

- Earlier PRs replaced by broader, newer PRs with validated outcomes.
- Split implementations where one branch has become the authoritative path.

### convert to issue

- Exploration or proposal PRs that should become tracked tasks.
- Partial implementations blocked by dependency, policy, or product decisions.

### needs owner review

- PRs touching protected branch checks, deployment, auth, tenancy, billing, or security.
- PRs with unresolved review threads or ambiguous architectural impact.

## Target State

- 0 to 3 active PRs at any given time.
- No zombie branches without owner or explicit closure date.
- Merge discipline:
  - one intent per PR
  - clear rollback path
  - required checks green before merge
  - stale triage cadence every week

## Suggested Phase 2 Process

1. Export all open PR metadata (age, owner, labels, checks, touched paths).
2. Classify each PR using the categories above.
3. Close or convert stale/superseded PRs with a standard comment template.
4. Keep only priority PRs tied to current release-readiness goals.
