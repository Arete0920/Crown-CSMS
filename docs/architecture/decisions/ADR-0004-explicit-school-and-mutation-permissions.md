# ADR-0004 — Explicit school and mutation permission authority

Status: Proposed; acceptance requires the governed pull-request merge path.
Date: 2026-10-07
Owner: CROWN repository owner

## Context

The central permission engine accepted missing school context by searching roles
across schools. Module permissions also reused read permission for mutations when
no write code was supplied. These defaults allowed new consumers to omit essential
security intent. Advancement seat reservation used that fallback; section-price
updates incorrectly invoked a decorator as a runtime permission checker.

## Decision

- Ordinary permission lookup requires an active authenticated principal and one
  explicit school. Missing scope denies; it does not combine school roles.
- A module permission without a write code is read-only. Mutations require an
  explicit action code. Action-only permissions such as scanning or imports name
  that action in both arguments.
- A generic role gate with no configured allowed roles denies.
- Advancement reservation and price mutations require advancement.edit.
- Disabled provider routes preserve their explicit view/edit hold contract and
  perform no provider-dependent mutation.
- Global Solomon catalog authoring retains its explicit staff/superuser path;
  a school role alone is not global catalog authoring authority.

## Alternatives and tradeoffs

Retaining permissive defaults with caller conventions was rejected: omissions
would continue to expand authority silently. Requiring a new permission taxonomy
for every existing action was deferred; this change uses the seeded permissions
and does not invent grants. Legitimate callers now must declare their write intent.

## Validation and evidence

The focused affected suite passed 163 tests with 16 subtests. One independent
PostgreSQL row-lock test was skipped on SQLite; its production-shaped proof remains
required. Regression tests cover absent scope, other-school grants, inactive users,
implicit mutation denial, explicit mutation success, unconfigured role gates,
seat-service nonexecution on denial, and successful authorized price updates.

Required GitHub gates must pass at the exact PR head before merge. Local tests are
not current-main, deployment, full-module, or PostgreSQL certification.

Control path: solo-maintainer policy, required GitHub checks, and retained CI
artifacts. Engineering implementation and evidence audit do not constitute
independent human approval.

## Rollback and compatibility

Revert this coherent PR if required; do not relax checks to obtain a merge.
No schema or data migration, role grants, provider activation, or deployment change
is included. Returning to permissive defaults restores the identified risks and
requires an explicit security disposition.
