# Canonical Household, Guardian, and Student Consumer Inventory

**Status:** Controlled architecture supporting record — canonical write authority accepted; governed student bridge implemented; compatibility retirement remains separately controlled  
**Effective date:** 2026-08-15  
**Accepted decision:** `docs/architecture/ADR-001-CANONICAL-HOUSEHOLD-GUARDIAN-STUDENT.md`  
**Related controls:** Issue #28, issue #14, `docs/architecture/STUDENT_IDENTITY_BRIDGE_CONTRACT.md`

## Purpose

This record defines the current identity-model authority and the implemented compatibility boundary. It records the completed Outcome B disposition from issue #28: an explicit, tenant-scoped, evidence-backed bridge between canonical `core.Student` and compatibility `households.Student`.

This record does **not** authorize destructive compatibility retirement, bulk identifier replacement, table renaming, silent identifier remapping, or migration of external identifiers without separately governed proof.

## Current write authority

`core.Family`, `core.Guardian`, and `core.Student` are the canonical operational write records for school-scoped family, guardian, and student identity.

That authority is supported by current dependency ownership:

- each canonical record belongs to `core.School`;
- `core.Student` participates in canonical operational enrollment/tuition/ledger and downstream student-domain workflows;
- `core.Family` and `core.Student` participate in financial relationships;
- `core.Guardian` participates in authenticated user relationships;
- new operational identity writers must use the canonical core authority unless a later accepted ADR explicitly replaces ADR-001.

The accepted decision establishes write authority. It does not assert that compatibility tables are empty, semantically identical, or removable.

## Persisted identity families

### Canonical operational family

`backend/core/models.py` defines the authoritative operational `Family`, `Guardian`, and `Student` records, including direct school ownership and lifecycle relationships used by core school operations.

### `households` compatibility domain

`backend/households/models.py` defines separate `Household`, `Guardian`, and `Student` persistence with its own UUID identities and school identifiers.

This domain remains active compatibility/read infrastructure for existing roster, Gradebook, billing, OneRoster, portal, reenrollment, and related consumers. It is not an approved canonical operational student writer and must not be removed or silently remapped merely because model names overlap.

### `crown_api` person/membership compatibility domain

`backend/crown_api/models_households.py` defines normalized `Person`, `Household`, `HouseholdMember`, and related structures used by compatibility/API flows. This domain is not interchangeable with the canonical core family.

### Guardian-household wizard session domain

`backend/guardian_household_wizard/models.py` stores tenant-bound workflow session state and JSON payloads. It coordinates workflow; it is not an independent identity authority.

## Implemented student identity bridge — Outcome B

Issue #28 selected and implemented **Outcome B: explicit governed bridge** rather than a destructive first-step migration of `academics.Enrollment.student`.

`core.StudentIdentityLink` is the approved student-level crosswalk between canonical `core.Student` and compatibility `households.Student`.

The persisted bridge enforces:

1. an owning `core.School`;
2. one-to-one canonical `core.Student` identity;
3. one-to-one compatibility `households.Student` identity;
4. same-school validation on both sides;
5. protected deletion semantics on both student references;
6. explicit mapping source;
7. explicit verification state;
8. an evidence reference before a mapping can be marked verified.

The migration authority is `backend/core/migrations/0013_student_identity_link.py`. The behavioral contract is `docs/architecture/STUDENT_IDENTITY_BRIDGE_CONTRACT.md`.

### Prohibited matching

No active path may create or promote a verified cross-family identity based solely on:

- UUID coincidence;
- first/last name;
- email;
- grade;
- household or family membership alone;
- list position or date ordering;
- fabricated/substituted date of birth;
- any heuristic composite without explicit authoritative provenance.

Unmapped, pending, cross-school, or otherwise unverified identities remain explicit and fail closed where canonical identity is required.

## Current bridge consumers and dispositions

### Admissions / applications — BRIDGE + CANONICAL WRITER

Application acceptance provisions canonical `core.Student` identity and compatibility identity under one transaction and creates/reuses an evidence-backed `StudentIdentityLink`. Active enrollment-state/admissions conversion routes require verified identity rather than name matching, fabricated student numbers, or substituted DOB values.

Disposition: **CANONICAL operational identity writer with explicit compatibility bridge**.

### Student360 — BRIDGE

Active scoped Student360 routes authorize the compatibility profile first where required by the existing portal model, then promote to canonical `core.Student` output only through a same-school VERIFIED `StudentIdentityLink`. Pending or unmapped records are not heuristically promoted; cross-school bridge corruption does not authorize cross-tenant resolution.

Disposition: **BRIDGE / fail-closed canonical promotion**.

### Attendance — CANONICAL WRITE THROUGH BRIDGE

Section Attendance writes persist canonical `core.Student` plus canonical `academics.Section`. A submitted student ID must resolve through exactly one same-school VERIFIED bridge with evidence, and the mapped compatibility student must be enrolled in the submitted canonical section before any write occurs.

Disposition: **CANONICAL write authority with bridge-backed roster membership proof**.

### Scheduling / academics roster — COMPATIBILITY RETAINED

`academics.Enrollment.student` continues to reference `households.Student`. This is an intentional compatibility boundary, not a statement that `households.Student` is canonical identity authority. The existing roster relationship remains stable while downstream consumers are migrated deliberately.

Disposition: **COMPATIBILITY / retained behind governed bridge**.

### Gradebook — COMPATIBILITY RETAINED

`gradebook.GradeEntry.student` continues to reference `households.Student`, and Gradebook roster relationships consume `academics.Enrollment`. Gradebook action-level mutation authority and roster integrity are governed separately.

Disposition: **COMPATIBILITY pending separately governed consumer migration**.

### Billing — COMPATIBILITY RETAINED

Current tuition billing derives enrolled compatibility students and household grouping from `academics.Enrollment`. This dependency is retained intentionally; it does not change canonical student write authority.

Disposition: **COMPATIBILITY pending separately governed financial-consumer migration**.

### OneRoster — EXTERNAL-ID COMPATIBILITY RETAINED

OneRoster currently exports compatibility student/enrollment IDs as sourced identifiers. Those identifiers have external continuity implications and must not be silently replaced with canonical `core.Student` IDs.

Disposition: **COMPATIBILITY / external-ID continuity boundary**.

### Seed/demo/sandbox — EXPLICIT FIXTURE BRIDGE

The Heritage sandbox creates explicit paired canonical/compatibility student fixtures and VERIFIED `StudentIdentityLink` records with sandbox provenance before creating compatibility roster enrollment. Sandbox fixture identity is evidence for product behavior only and is not production mapping authority.

Disposition: **BRIDGE fixture / non-production evidence only**.

## Reconciliation evidence

`python manage.py reconcile_student_identities` is intentionally read-only and performs no candidate matching or writes. Per school it reports:

- canonical student total;
- compatibility student total;
- mapped total;
- verified total;
- pending total;
- unmatched canonical total;
- unmatched compatibility total;
- invalid cross-tenant links;
- ambiguous candidates as `not_inferred`.

This command is the required starting evidence for any later compatibility-retirement or destructive-convergence proposal.

## Issue #28 disposition

The identity/roster boundary required by issue #28 is **COMPLETED AND VERIFIED** through the governed bridge architecture.

The following required properties are implemented and regression-proven:

- same-school verified mappings resolve deterministically;
- cross-school mappings are rejected or fail closed;
- one-to-one uniqueness rejects duplicate mappings rather than guessing;
- pending/unmapped identities are not heuristically promoted;
- Attendance proves canonical section membership through the verified bridge;
- Student360 preserves tenant-safe, nondisclosing identity behavior;
- Admissions creates/reuses canonical identity with explicit provenance;
- Heritage seed/demo behavior uses explicit evidence-backed fixture links;
- Scheduling/Gradebook/Billing/OneRoster compatibility identities remain explicitly classified rather than silently redefined.

No direct `academics.Enrollment.student` FK replacement is required to satisfy this disposition. That would be a separate high-blast-radius migration and is not authorized by issue #28 closure.

## Compatibility retirement remains separate

Closing issue #28 does **not** certify full compatibility-table retirement or data equivalence across every tenant. Before any destructive convergence or external-ID replacement, a separately governed repair must still produce production-shaped non-production evidence including:

1. tenant-by-tenant mapped/unmapped/duplicate/orphan/referential-integrity counts;
2. explicit disposition of every unexplained row;
3. migration timing/locking assessment;
4. representative Scheduling, Gradebook, billing, OneRoster, portal, reporting, import/export, and analytics regression proof;
5. rollback or forward-fix rehearsal;
6. external-ID continuity proof where integrations expose compatibility identifiers;
7. exact-head governed review and certification for the proposed migration.

Until that proof exists, compatibility persistence is retained intentionally and the bridge remains the approved translation boundary.

## Constraints

- No destructive migration by inference.
- No table rename solely because models share names.
- No silent ID remapping or cross-tenant merge.
- No heuristic identity promotion.
- No compatibility bridge removal before reconciliation evidence.
- Tenant isolation remains fail closed.
- New operational student identity writes follow canonical `core.Student` authority unless a later accepted ADR replaces ADR-001.

## Current disposition

- Canonical operational family/guardian/student write authority: **ACCEPTED**.
- Governed `StudentIdentityLink` bridge: **IMPLEMENTED AND VERIFIED**.
- Admissions canonical identity provisioning: **IMPLEMENTED AND VERIFIED**.
- Student360 verified-bridge resolution: **IMPLEMENTED AND VERIFIED**.
- Attendance canonical section membership through bridge: **IMPLEMENTED AND VERIFIED**.
- Existing roster/Gradebook/Billing/OneRoster compatibility identities: **RETAIN / EXPLICIT**.
- Issue #28 identity/roster bridge objective: **COMPLETED AND VERIFIED**.
- Destructive compatibility retirement: **NOT AUTHORIZED / SEPARATE FUTURE GOVERNED WORK**.
