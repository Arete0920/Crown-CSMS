# Family absence review

Decision owner: TC Megahan. Baseline: `d3d0c97f433e572736450485e30f90dec242ad76`.
The owner authorized completion of the reviewed school-workflow improvements.

## Workflow and authority

Parents submit a dated absence explanation through classroom records. The submission
does not write attendance. An assigned teacher or school leader selects the classroom
and roster date in classroom operations, reviews the explanation, and records a reason
shared with the family. An excuse changes an existing ABSENT or EXCUSED record to
EXCUSED; declining leaves its current status intact. Neither action creates attendance
for an unmarked student or overrides PRESENT/TARDY. Ordinary corrections remain in the
existing audited attendance workflow.

The review uses the canonical attendance record and requires the verified compatibility
student-to-Core identity link. The classroom record, attendance audit, and classroom
follow-through event commit together. Expected explanation and attendance versions
prevent stale writes. Existing operation retry keys preserve safe retries and reject
conflicting payloads. No additional attendance or identity store is introduced.

Substitutes retain authorized roll-call access but receive neither explanation bodies
nor review authority. School, section, active student and enrollment relationships
constrain both reads and writes. The pending queue includes the selected absence date
and undated historical records; a reviewer must explicitly confirm the selected date
for an undated explanation. It never infers a date from prose. Lists are bounded at
100 with full queue counts. Resolved explanations leave the queue; families can read
the decision through their existing scoped classroom history.

## Verification and rollback

Regression scenarios cover parent submission without an attendance write, excuse and
decline, safe retries, stale versions, date mismatches, unmarked/present/tardy records,
undated confirmation, unauthorized parent/substitute requests, cross-school records,
inactive students, unverified identities and family-visible decisions. Interface tests
cover reason requirements, both versions, date confirmation, disabled review and limits.

Verification follows the approved solo-maintainer path, not independent human review.
Exact-head security, tenant, backend, frontend and release gates remain unchanged.
No schema or dependency change is required. Rollback is a code revert; existing
append-only review history remains evidence. Hosted deployment remains separate.
