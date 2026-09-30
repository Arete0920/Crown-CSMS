# Production Release Top 10 Remaining Tasks - 2026-05-28

> Authority Scope Notice (2026-05-29)
>
> This document is a ranked operational closure backlog and not a controlling repository-level release authority source.
>
> Current controlling sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

## Purpose

This list ranks the remaining work needed to reach a credible 95+ production-release-ready posture. It is scoped to the current approved release slice and does not expand production claims to draft or unreleased work.

## Ranking Criteria

- Blocks unrestricted GO first.
- Reduces contradictory authority risk next.
- Improves proof freshness and release confidence next.
- Excludes draft, unmerged, or future-module claims.

## Top 10 Remaining Tasks

| Rank | Task | Severity | Owner | Why it matters | Proof required to close |
| --- | --- | --- | --- | --- | --- |
| 1 | Close deploy SHA parity for the release target | Critical | Solo owner | This is the largest explicit blocker in the canonical status stack and prevents unrestricted GO. | Latest parity packet proves the deployed runtime SHA matches the approved release target SHA and is linked from `docs/CURRENT_RELEASE_STATUS.md`. |
| 2 | Finish authority convergence across legacy release docs | Critical | Solo owner | Conflicting or ambiguous authority language still prevents a clean unconditional release posture. | All legacy GO/PARTIAL/FAIL docs are clearly labeled historical or operational, with one canonical authority source remaining. |
| 3 | Re-run runtime and policy proof on the exact candidate SHA | Critical | Solo owner | Release confidence depends on proof on the exact candidate SHA, not just nearby evidence. | Green protected-spine runtime packet plus green policy gates on the exact release-candidate SHA. |
| 4 | Refresh live Azure backend smoke evidence | High | Solo owner | The current review does not include a fresh live Azure smoke, so runtime claims remain bounded to existing evidence. | Fresh live backend health smoke, captured against the approved slice and recorded in the release evidence stack. |
| 5 | Keep billing golden path regression coverage green | High | Backend lead / QA | Billing had a recent fixture correction history, so it needs persistent release-slice regression attention. | Passing billing golden-path tests on the current mainline plus recorded evidence in the release packet. |
| 6 | Keep admissions golden path regression coverage green | High | Backend lead / QA | Admissions is core to the approved release slice and must remain stable for production release claims. | Passing admissions golden-path tests on the current mainline plus recorded evidence in the release packet. |
| 7 | Keep frontend truth-disclosure smoke green | High | Frontend lead / QA | Truth-disclosure is part of the release posture and must stay aligned with live/fallback/unavailable states. | Passing frontend smoke covering truth-disclosure behavior and current dashboard surfaces. |
| 8 | Keep backend/frontend/tenant proofs fresh after material changes | High | All leads | The current proof is green, but it can stale quickly after code changes. | Re-run of backend check, tenant/RBAC tests, frontend build/tests, and relevant route checks after any material change. |
| 9 | Maintain strict no-scope expansion for unreleased modules | High | Product + release owner | Mentioning draft scheduling, SOLOMON ingestion, publisher activation, or unsupported client-facing automation claims would overstate production readiness. | Updated release docs keep the exclusion list explicit and no production claims reference excluded modules. |
| 10 | Keep OpenAPI export and public/CSRF policy proof in the release loop | Medium | Backend lead / QA | These are core governance proofs that help prevent regressions and support release confidence. | Successful OpenAPI export, public-endpoint policy validation, and CSRF exception validation on the current release slice. |

## Notes

- Items 1 through 3 are the direct blockers to an unrestricted GO claim.
- Items 4 through 10 are the release-confidence and proof-freshness controls needed to sustain a 95+ posture.
- Draft or unmerged modules are excluded from production claims until separately merged, tested, and gate-proven.

## Out-of-Scope For This List

- Scheduling PR #859 as a production claim.
- SOLOMON ingestion or client-facing automated-intelligence activation.
- Publisher content activation.
- Any feature without hosted green gates.
