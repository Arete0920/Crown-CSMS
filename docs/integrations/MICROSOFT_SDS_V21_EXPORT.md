# CROWN Microsoft School Data Sync v2.1 Export

**Status:** implementation candidate; Microsoft tenant import not yet certified  
**Scope:** one CROWN school, one active academic term, existing Microsoft accounts only

## Purpose

This integration produces the five-file Microsoft School Data Sync (SDS) v2.1
CSV class-roster package from CROWN records:

- `orgs.csv`
- `users.csv`
- `roles.csv`
- `classes.csv`
- `enrollments.csv`

The package is a real ZIP archive and the same five-file set is emitted every
time. CROWN remains authoritative for school, section, enrollment, and teacher
assignment records. Export does not create or change Microsoft 365 objects.
A successful export is persisted in the canonical CROWN audit log with actor,
school, term, file set, and aggregate counts; no student names or cloud usernames
are copied into the audit metadata.

## Endpoint

```text
GET /api/integrations/microsoft/sds-v2.1/export/?term_id=<academic-term-uuid>
X-School-Id: <school-uuid>
```

The caller must be authenticated and hold the existing school-scoped
`rosters.edit` permission for the selected school. Cross-school authorization
continues to use the canonical CROWN tenant contract.

## Identity matching

This first release assumes that the corresponding Microsoft accounts already
exist. It does not create users.

- Students are exported only when they are active, enrolled in a section for the
  selected term, and linked to a CROWN authenticated account with a
  domain-qualified email/username.
- Teachers are exported from active `core.Staff` records that have an
  `academics.TeacherAssignment` in a selected section.
- The normalized domain-qualified value is emitted as `username` and `email`.
  The first Microsoft test flow must explicitly match SDS `Username` to Microsoft
  Entra `UserPrincipalName`; this release does not invent a separate immutable
  Microsoft identifier.
- If a required identity is missing or if two CROWN identities resolve to the
  same cloud username, export fails. It does not guess.

Stable SDS `sourcedId` values are derived from CROWN UUIDs:

```text
school:<school UUID>
student:<student UUID>
staff:<staff UUID>
section:<section UUID>
```

## Data boundaries

The exporter deliberately omits optional `academicSessions.csv` and
`courses.csv` references in this release. Class rows therefore do not emit
`sessionSourcedIds` or `courseSourcedId`. This keeps the first delivery to
the required SDS v2.1 class-roster set and avoids introducing unresolved
optional-file dependencies.

No guardian data, grades, assignments, Teams provisioning, Microsoft account
creation, licensing, or Microsoft sign-in behavior is part of this release.

## Pre-import validation

Before any Microsoft test import:

1. Use a non-production education tenant and synthetic or specifically
   authorized test identities.
2. Confirm the school and term IDs.
3. Confirm the expected class, student, and teacher counts shown in the response
   headers.
4. Inspect the ZIP and verify the exact five file names.
5. Confirm every `users.csv.username` value maps to the intended Microsoft
   account.
6. Preserve the exact ZIP that will be imported as evidence for reconciliation.

A CROWN export passing tests is not proof that Microsoft accepted or applied the
package.

## Microsoft test acceptance

The release is Microsoft-verified only after all of the following are recorded:

- SDS accepts all five files and their headers.
- Imported school/class/user references reconcile to the expected CROWN IDs.
- Student and teacher class memberships match the CROWN source counts.
- Re-uploading the same package creates no duplicate users/classes/memberships.
- A controlled CROWN membership change appears correctly after a subsequent
  complete five-file upload.
- No unrelated Microsoft organization, user, class, or membership changes.

## Recovery

CROWN export is read-only. Reverting or disabling the CROWN endpoint does not
undo a prior Microsoft import.

For a test import, retain:

- the previous accepted five-file package;
- the package under test;
- expected membership counts;
- the SDS run/result identifiers;
- the exact CROWN commit SHA used to generate the package.

If reconciliation is wrong, stop additional uploads, preserve the SDS error/run
evidence, correct the CROWN source or export defect, and use the Microsoft SDS
test workflow to restore the known-good complete file set. Do not submit a
partial replacement set.

## Completion claim

Use these terms precisely:

- **Export candidate** — CROWN code and required repository checks pass.
- **Imported** — Microsoft SDS accepted the package.
- **Verified test release** — Microsoft-side records, repeat import, membership
  change, and recovery evidence all reconcile.

Do not call this integration complete from source or CI evidence alone.
