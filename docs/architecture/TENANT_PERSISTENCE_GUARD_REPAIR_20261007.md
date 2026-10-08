# Tenant persistence guard repair — 2026-10-07

Scope: TenantScopedModel and its Classroom/GraduationRule consumers.
Status: implemented on the repair branch; exact-head CI and governed merge pending.

## Implemented boundary

Individual save/delete and bulk create/update require explicit tenant_context.
Persisted ownership cannot move between schools through instance save, queryset
update, bulk update, or bulk conflict-update fields. Mixed-school bulk inputs are
validated before insertion/update. Reads retain the established missing-context
empty-queryset behavior. Supported seed commands enter explicit context and reject
invalid, inactive or ambiguous school selection rather than guessing the first row.

The shared guard applies only to subclasses. It does not establish that every
other model, raw SQL, base manager, import, or administrative path is tenant-safe.
Complete model/consumer registry verification remains required.

## Evidence and control path

Focused suite: 37 passed. Two existing classroom API tests skipped because their
optional seed-school prerequisite is absent; these skips are not classroom runtime
acceptance. Tests prove missing-context denial, mixed-tenant bulk rejection without
partial mutation, immutable school ownership, instance deletion scope, context
restoration, and explicit/idempotent seed behavior.

Control path: current solo-maintainer policy, exact-head required GitHub checks and
retained artifacts. Engineering support is advisory; local tests are not independent
human approval or deployed-runtime evidence. ADR-0001 and ADR-0003 remain the context
authorities. No schema/data migration or provider activation is included.

Rollback: revert this coherent repair, accepting restoration of the previous guard
inconsistencies only under explicit security disposition. Do not weaken CI gates.
