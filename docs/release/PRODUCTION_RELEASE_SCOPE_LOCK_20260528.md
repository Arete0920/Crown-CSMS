# Production Release Scope Lock - 2026-05-28

## Scope Statement

The current approved production release scope is the release-governed mainline slice only. Production claims must remain tied to the latest green mainline gates and live runtime proof.

## Included Scope

- Current release-governed mainline slice.
- Backend and frontend slices already proven green on mainline.
- Hosted gate evidence already attached to the release authority stack.
- Public endpoint and CSRF policy enforcement already verified.
- Truth-disclosure behavior already verified on the approved release surfaces.

## Excluded Scope

- Draft or unreleased scheduling work.
- SOLOMON ingestion.
- AI or client-facing intelligence activation.
- Publisher integrations.
- Curriculum ingestion.
- Any unmerged PR work.
- Any feature not already merged, tested, and gate-proven on mainline.

## Evidence Required Before Expanding Scope

Before any new module can be described as production-ready, all of the following must be true:

- The work is merged to the release-governed mainline.
- The work has matching test coverage.
- The work has hosted or runtime gate proof.
- The work has no contradictory release authority statements.
- The work is included in the canonical release status and scorecard.

## Rule

No future module may be described as production-ready until it is merged, tested, and gate-proven.

## Practical Guardrail

If a module is still draft, unmerged, or only partially proven, it may be discussed as planned, in progress, or unreleased, but never as production-ready.
