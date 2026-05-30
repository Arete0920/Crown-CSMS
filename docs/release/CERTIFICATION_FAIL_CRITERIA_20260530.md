# Certification Fail Criteria (2026-05-30)

Purpose: fail-closed criteria for fake-ready, placeholder-ready, or unverifiable release claims.

## Hard Fail Conditions

1. Placeholder/future copy appears on any route or dashboard marked ready/live/production.
2. Ready-state entry is missing required evidence object metadata.
3. Evidence branch mismatches canonical release authority branch.
4. Evidence candidate SHA mismatches canonical candidate SHA.
5. Required certification matrices or not-proven register are missing or stale.
6. Any required gate validator exits non-zero.

## Fail Verdict Rule

- Any hard fail condition immediately forces FAIL/NOT_PROVEN verdict.
- No subjective override is allowed without updated machine evidence.
