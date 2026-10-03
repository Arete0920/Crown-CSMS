# Family weekly agenda

## Problem and behavior

The family digest previously listed class assignments once, without identifying each
enrolled child, and filtered on the class due date. An approved individual deadline
could therefore disagree with Student Work or omit an assignment from the family's
seven-day window.

The parent digest now contains one item per authorized child and published assignment.
Each item includes the child, course, effective deadline, class deadline, public makeup
instructions, home support, and recorded submission state. Parents can view all children
or filter the displayed items to one child. Draft work and confidential adjustment
reasons are excluded. A submission timestamp is a receipt, not a grade or a completion
claim after work has been returned for revision.

## Authority and access

- `academics.Assignment`, `academics.Enrollment`, `academics.Submission`, and
  `academics.ClassroomDeadlineAdjustment` remain the data sources.
- Existing `classroom_scope` determines authorized students and sections, including
  guardian disclosure restrictions, active students, and active households.
- School and relationship scope also constrain the agenda queries. Malformed
  cross-school enrollments, category links, and submission/section links do not expand access.
- No identity writer, copied calendar, new persistence model, payment activation,
  external provider, or schema migration is introduced.
- The window uses the account's saved notification timezone, or the existing school
  request timezone when no preference exists.
- The visible list is limited to 100 child-assignment pairs, ordered by effective
  deadline and child. Total items and receipt counts cover the full window; truncation
  is explicit. Undated assignments are available through Student Work, not this digest.
- Teacher and administrator digests retain their class summary behavior.

## Validation and rollback

Focused tests cover siblings, distinct deadlines and receipts, extensions entering and
leaving the window, guardian restrictions, tenant scope, inactive students, unpublished
work, list limits, timezone boundaries, and empty windows. Interface checks cover child
filtering, adjusted deadlines, returned-work labels, truncation, and staff summaries.

Decision owner: TC Megahan. Implementation is authorized by the owner; verification and
diff review follow the approved solo-maintainer path, not independent human review.
Rollback is a revert of this change; no data or migration rollback is needed.
Exact-head CI is required before merge. Hosted deployment and notification transport
remain separate operational evidence.
