# CROWN Final Sprint Integrity Operating Standard - 2026-05-30

Status: ACTIVE FINAL-SPRINT CONTROL ARTIFACT
Authority: Non-shipping control artifact until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Purpose

This standard records how final sprint work must be performed. It exists to prevent avoidable errors, inflated status claims, speculative fixes, dirty source hygiene, and production-readiness claims that are not backed by current evidence.

## Product objective

CROWN is a faith-based, mission-driven Christian School Management Solution. The product objective is to exceed industry standards through stronger workflow design, clearer role journeys, truthful data, clean architecture, and values-aligned product behavior.

## Target dates

| Milestone | Target | Integrity condition |
|---|---|---|
| Sandbox-ready process | 2026-06-01 | Only if sandbox evidence passes and sandbox limitations are explicit |
| Production marketplace release | 2026-07-01 | Only if every final release gate is complete, current, and 95+ |

Calendar targets do not override evidence. If proof is missing, status remains `NOT DONE`.

## Non-negotiable rules

1. No guessing.
2. No assumed completion.
3. No imagined status.
4. No production claim from file, route, registry, or dashboard presence alone.
5. No broad code edits without reading the relevant source first.
6. No release-authority promotion without current candidate-SHA evidence.
7. No hidden partials, deferrals, or placeholder production surfaces.
8. No stale evidence used as current proof.
9. No bypassing first-failure triage.
10. No score increase without direct proof.

## Evidence labels

| Label | Meaning |
|---|---|
| VERIFIED | Current repo, CI/runtime output, committed evidence, or explicit terminal proof supports the claim |
| NOT VERIFIED | Present or plausible but not proven by current evidence |
| NOT DONE | Incomplete, weak, noisy, deferred, unproven, or below 95 |
| PASS | Current evidence proves the required gate or row |
| FAIL | Current evidence proves the gate or row is broken |

## Required work method

Before changing source code:

1. Read the relevant files.
2. Identify the exact contract being changed.
3. Make the smallest safe change.
4. State the evidence required to prove it.
5. Avoid unrelated changes.

After changing source code:

1. Run the narrowest relevant proof first.
2. Capture output.
3. Broaden proof only after narrow proof passes.
4. Commit evidence honestly.
5. Do not update release authority until all required gates pass.

## Faith and mission design guardrails

CROWN should reflect Christian school priorities through stewardship, service, clarity, trust, family partnership, pastoral care, mission alignment, academic excellence, operational order, and truthful reporting.

Mission language must never hide operational weakness. The product must be more truthful because of its mission, not less.

## Competitor-learning guardrail

Competitor research may inform workflow expectations, KPI design, role journeys, and usability standards. The goal is to learn industry patterns and exceed them through original execution.

## Source hygiene guardrail

The codebase must be treated as a production source system:

- stale release language must be removed or clearly superseded,
- duplicate implementations must be avoided,
- dead routes and fake-ready pages must be eliminated or hidden,
- compatibility routes must be classified,
- documentation must match current evidence,
- commits must stay scoped,
- known gaps must not be buried under optimistic wording.

## Partnership rule

The architect/designer/auditor role is to tell what is true and what is needed. If a gate is red, say it is red. If a module is unproven, say it is unproven. If work is not shippable, do not call it shippable.
