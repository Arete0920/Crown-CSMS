# ADR-001: Canonical Household, Guardian, and Student Identity Spine

**Status:** Accepted for operational writes  
**Date:** 2026-07-16  
**Issues:** #1353, #1381

## Decision

`core.Family`, `core.Guardian`, and `core.Student` are the canonical operational identity records for school-scoped household, guardian, and student writes.

The decision is based on verified dependency ownership rather than model names:

- each record has a real `core.School` foreign key;
- `core.Student` is referenced by enrollment and tuition;
- `core.Family` and `core.Student` are referenced by the ledger;
- `core.Guardian` is referenced by authenticated user accounts;
- admissions already bridges the `core` records to the separate `crown_api` household/person records.

## Compatibility disposition

The following remain supported compatibility/read domains and are not deleted or renamed by this decision:

- `households.Household`, `households.Guardian`, and `households.Student`;
- `crown_api.models_households.Person`, `Household`, `HouseholdMember`, and `Student`;
- `core.HouseholdFamilyLink` and admissions compatibility references.

No writer may silently copy, merge, or remap identifiers between these domains. Migration or retirement requires tenant-by-tenant reconciliation and rollback proof under #1353.

## Guardian-household wizard write contract

The guardian-household wizard writes only to the canonical `core` family:

1. every selected student must exist in the active school;
2. all selected students must already belong to the same `core.Family`;
3. the wizard must never reassign a student to another family;
4. family details may be updated only inside the same transaction as guardian writes;
5. guardian identity is the existing `(school, email)` uniqueness contract;
6. an existing guardian attached to another family is a conflict, not a merge;
7. commit is idempotent through the locked wizard session and persisted `commit_result`;
8. any validation or database failure rolls back all family and guardian changes;
9. legacy `households` and `crown_api` identity tables receive no writes from this wizard.

## Tenant boundary

All reads and writes are constrained by the resolved active school. Foreign-school identifiers return a nondisclosing not-found validation result. Administrative header override behavior remains governed by the canonical tenant resolver.

## Consequences

- The broken legacy wizard mapping is removed from the active route.
- The wizard becomes an operational-family configuration flow, not a cross-model migration tool.
- Existing students are never silently moved between financial families.
- Full convergence of the compatibility domains remains a separate expand-contract migration under #1353.

## Required evidence

The implementing pull request must prove:

- same-school shared-family commit;
- deterministic repeated commit;
- no legacy identity writes;
- cross-school student denial;
- mixed-family rejection with no writes;
- guardian email conflict rejection with rollback;
- verify transition after commit;
- exact changed-file scope and exact-SHA CI completion.
