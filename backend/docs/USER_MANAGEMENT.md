# CROWN User Management and Roles

## Purpose

This document defines the verified user-role management contract for Module 003: User Management & Roles.

Module 003 proves that Crown users can be created, assigned roles, transitioned between roles, removed from roles, assigned in bulk, and constrained by tenant-scoped uniqueness rules.

## Canonical models

User management currently relies on:

- `UserAccount`
- `UserRole`
- `School`
- `CrownPermission`
- `RolePermission`

## Role assignment contract

A user receives role authority when a `UserRole` row exists for:

- the user
- the school / tenant
- the role code

Permissions are resolved by matching the user's school-scoped role codes to `RolePermission` rows.

## Tenant-scoped authority

A role assigned in School A must not grant authority in School B.

A user may hold different roles in different schools, but each role is scoped to its own tenant.

## Role transition contract

A role transition may be represented by changing `UserRole.role_code` or replacing one role row with another.

Expected behavior:

1. Permissions attached to the old role no longer apply after transition.
2. Permissions attached to the new role apply after transition.
3. Transitioned authority remains scoped to the school on the `UserRole`.

## Role removal contract

A user loses role authority when the relevant `UserRole` row is removed.

Removed roles must no longer grant permissions through `user_has_permission()`.

## Bulk role operation contract

Bulk assignment is valid when a school needs to assign the same role to a cohort of users.

Bulk role creation must preserve tenant scoping and must not grant authority outside the target school.

## Uniqueness contract

The same user may not receive the same role twice in the same school.

The same user may:

- hold the same role in different schools
- hold different roles in the same school

The enforced uniqueness key is:

```text
school + user + role_code
```

## Proof coverage

`backend/tests/test_user_management.py` proves:

1. user creation with role assignment

2. tenant-scoped permission grant

3. role transition removes old permission and adds new permission

4. user can hold distinct roles in distinct tenants without cross-bleed

5. deleted role can no longer act

6. bulk cohort role assignment

7. bulk assignment remains tenant scoped

8. duplicate same-school same-role assignment is rejected

9. same user can hold same role in different schools

10. same user can hold different roles in the same school

## Non-goals

This lane does not change authentication services, token issuance, password policy, session handling, login admission rules, or auth middleware.
