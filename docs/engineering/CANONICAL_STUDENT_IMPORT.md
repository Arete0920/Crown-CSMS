# Canonical student import contract

Base: `bd5bfcd0b392f499f9cae5f08e8c3964cfd725fd`.
Decision owner: repository product owner; implementation and necessary PR completion
are authorized by the current reviewed-workflow request.

## Scope recorded before implementation

Outcome: the existing import wizard previews, commits atomically and verifies actual
canonical students and their explicit compatibility identity links.
Allowed: student_import_wizard service, views, permissions, model/retention migration
and tests; required wizard-contract permission fixture; existing StudentImportWizard
page and interface tests; this contract; existing PostgreSQL verification coverage.
Forbidden: family/household/account creation, names/emails as identity matching,
financial/attendance/grade writers, external delivery, dependencies and deployment.
Rollback: revert the code and retain committed session evidence and identity links.
Do not delete imported students as a code rollback. Earlier sessions need explicit
reconciliation before being represented as verified canonical migrations.
Not verified: deployed import, source-provider export completeness, historical grade
migration, full backup/restore or legal data-portability compliance.

## Required canonical evidence

School-scoped roster editors supply student number, first/last name, birth date,
status, canonical family ID and compatibility household ID. Grade code is optional.
The selected family and household must have an explicit same-school family bridge.
No identity or household is guessed or generated from names. New canonical students
receive one verified compatibility identity link with import-session provenance.
Explicit compatibility IDs reconcile existing unmapped household students; an
existing canonical student without its verified identity link requires that explicit
mapping. Names validate the provided mapping but never select a record. Duplicate
compatibility IDs and identities already assigned elsewhere fail closed.
Existing student numbers identify the same-school canonical record. Family/birth-date
conflicts require separate review rather than automatic identity reassignment.

Preview has no student writes. It validates every row, school relationship, field,
status and duplicate identifier, and includes before/after states plus a fingerprint.
Commit requires the reviewed fingerprint and a reason, revalidates under transaction
locks and rejects changed evidence. Any failed row rolls back all student/link writes.
Session/fingerprint retries return the recorded result without duplicate students.
Verification compares actual canonical and compatibility rows with committed evidence.
It reports reconciliation needs when rows or mappings subsequently change.

## Review and operation

Each batch is bounded to 1,000 rows; the interface exposes every proposed change in
100-row pages. Unmapped optional grades preserve existing school grade authority;
an explicitly mapped blank grade clears it after review. Student numbers remain
strings, including leading zeros. The old external_id column target is an explicit
alias for canonical student_number, not a separate compatibility identity field.

Roster-edit permission, an active account and an explicit school header govern every
step. The wizard does not create family, household or authenticated account records,
and it does not create course enrollments, grades, attendance or financial records.
The selected household/family bridge must already exist in the correct school.

The interface requires a review reason and confirmation; unresolved rows block all
writes. A saved batch with unavailable verification remains pending, with a dedicated
verification retry. Changed records are labeled for reconciliation rather than done.
Denied access hides record previews; network failures retain the reviewed payload.
Committed configuration, preview and result evidence cannot be rewritten through model
saves/bulk updates or deleted by the workflow. Session school/creator relationships
protect retained evidence. No historical session is silently upgraded into new proof.

The schema change strengthens retention on existing session relationships. Reverting
code does not undo recorded imports or erase their session/identity evidence. Data
corrections require a separately reviewed import or authoritative correction workflow.
