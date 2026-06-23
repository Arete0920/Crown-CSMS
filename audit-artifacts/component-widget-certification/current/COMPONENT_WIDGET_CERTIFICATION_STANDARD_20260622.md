# Component and Widget Certification Standard

Date: 2026-06-22
Branch: cleanup/live-authority-rebaseline-20260622
Purpose: document component/widget certification without creating new product scope or false blockers.

## Certification posture

The working assumption is that components and widgets are already covered by the completed module, dashboard, and wizard evidence where they are embedded in those certified surfaces.

This lane exists only to make that coverage explicit.

## Rules

A component or widget may be marked certified only under one of these categories:

1. `CERTIFIED_BY_DASHBOARD_SCOPE`
   - The component/widget is part of a dashboard that is certified in `audit-artifacts/dashboard-completion/state/dashboard-certification-state.json`.

2. `CERTIFIED_BY_WIZARD_SCOPE`
   - The component/widget is part of a wizard covered by the GitHub Actions wizard parity and 50-wizard assertion evidence.

3. `CERTIFIED_BY_MODULE_SCOPE`
   - The component/widget is part of a module with 51/51 PROVEN evidence in `audit-artifacts/module-completion/current/05_completion_scorecard.md`.

4. `INFRASTRUCTURE_COMPONENT`
   - The component is shared shell/routing/layout/design infrastructure and is covered by module 008 Shared Frontend Shell, module 009 Shared Design System, dashboard certification, frontend shell certification, or related CI evidence.

5. `NOT_PRODUCT_SURFACE`
   - The file is not a user-facing product component/widget, or is test/support/dev-only.

## Required evidence fields

Each certified row must record:

- item name;
- item type: component, widget, dashboard card, metric block, layout shell, route guard, utility component;
- source path;
- owning surface: module, dashboard, wizard, shell, or support;
- certification category;
- evidence pointer;
- final status.

## Final status values

Allowed final statuses:

- `CERTIFIED`
- `CERTIFIED_BY_PARENT_SURFACE`
- `NOT_PRODUCT_SURFACE`
- `NEEDS_REVIEW`

No row may be described as complete with vague language such as probably, likely, assumed, or covered somehow.

## Current expected closeout

The expected closeout is not new engineering work. It is documentation of existing coverage:

- modules already certified/proven;
- dashboards already certified for internal dashboard scope;
- wizards already certified by GitHub Actions evidence;
- embedded components and widgets certified by those parent surfaces unless they are independent product surfaces requiring separate treatment.

## Non-claims

This standard does not claim production GO, pilot GO, unrestricted sandbox GO, or independent human review.
