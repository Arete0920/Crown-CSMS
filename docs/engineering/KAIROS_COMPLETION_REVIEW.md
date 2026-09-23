# Kairos scheduling completion review

Base: `e670a8701f37c4e30182454ab20bbe8e28809f11` in `Arete0920/Crown-CSMS`.
Disposition: implementation prepared for review; full application CI and deployed runtime NOT VERIFIED.

## Delivered changes

- Versioned edits to existing placements; stale edits rejected at staging and publication.
- Explicit removal and movement retain inactive records; other meetings remain active.
- Atomic undo with before/after receipt, version checks, and current conflict revalidation.
- Room capacity, shared-student, teacher, room, section-overlap, and noninstructional-period checks.
- Scheduling permissions for bell schedule configuration and publication.
- Student schedule reads use existing verified StudentIdentityLink mappings; no heuristic matching or new schema.
- Self-service schedule endpoint returns the signed-in student's or teacher's published recurring meetings.
- Teacher/student cards use that endpoint instead of fixed sample classes, with loading/empty/error states.
- Kairos page uses named years/terms, existing meeting selections, explicit removal/undo, and the approved logo.
- Publication remains visible and undoable if post-publication verification fails.

## Verification and limits

66 focused backend tests and 7 frontend interaction tests passed in the isolated environment. The final backend rerun after compatibility additions also passed all 66 tests. The isolated Django system check passed.

Backend tests use real repository models, application configs, tenant resolver, permission registry, services, and API views, SQLite, and --nomigrations. The harness installs only relevant application domains. Frontend tests mount the actual changed components in jsdom while mocking layout and API transport. This is not full production middleware, full application build, Postgres concurrency, migration, authenticated browser, or deployed runtime proof. Those remain required before release. New tests are normal repository tests, runnable under the standard complete checkout.

Run in a full checkout:

```
python backend/manage.py check
python -m pytest backend/bell_schedule_wizard/tests backend/section_scheduler_wizard/tests backend/crown_api/tests/test_scheduling_api.py backend/crown_api/tests/test_scheduling_canonical_adapter.py backend/crown_api/tests/test_scheduling_multi_meeting_adapter.py --nomigrations --tb=short
cd frontend/dashboards
npm run test -- --run src/pages/SectionSchedulerWizard.test.jsx src/components/dashboard/scheduling/PublishedScheduleCard.test.jsx
npm run build
```

## Optimizer requirements disposition

No working optimizer was established in the inspected scheduling paths. This change adds no optimizer or automated schedule-generation claim.

| Capability | Current disposition | Required next implementation |
|---|---|---|
| Placement of existing classes | Implemented and focused-tested | Full application integration proof |
| Student conflicts and capacity | Enforced for current canonical enrollments | Revalidate when enrollment changes after publication |
| Chapel/devotions | Noninstructional blocks protected | School must mark its protected blocks in bell setup |
| Teacher availability and maximum workload | No established policy/model in inspected scheduler | Define and persist availability, prep periods, workload units and limits |
| Course requests and ranked electives | Not established | Request model, priorities, prerequisite checks and demand inputs |
| Automatic placement | Not established | Deterministic solver, infeasibility explanations and time limits |
| Scenario comparison | Not established | Scenario snapshots, objective scores and approved publication |
| Standalone imports/exports | Not established | Tenant-safe format, validation, reconciliation and portable exports |
| Calendar interpretation | Recurring templates only | Map template rotations to actual dates before claiming a daily schedule |

## Important operating boundaries

- Existing room uniqueness is school/year/room/template/block based, without a term field. Shared blocks across disjoint terms may still be rejected by the database. A separately scoped schema change is needed if that is required.
- Student and staffing edits in other modules can invalidate a previously published schedule; this PR validates at publication and undo, not every cross-module mutation.
- StudentIdentityLink must be verified and have evidence. Unlinked students retain the existing bounded legacy schedule behavior; self-service cards show an empty state.
- The generic legacy household access resolver remains unchanged. Broader identity/access convergence is outside this bounded change.
- The advanced page shows recurring meetings. It does not claim today's actual calendar interpretation.
- A school must reload the page after changing its active school selection unless the shell remounts the component; full shell integration must verify this.
- Old publications retain verification support but have no undo receipt.

## Existing dependency gate

The August 21 pip-audit log for job 96892623313 reports Django 5.2.16 / PYSEC-2026-3717 (CVE-2026-15830), with 5.2.17 listed as a fix. This is a pre-existing dependency issue. No dependency pins or scanner workflows were changed in this scheduling PR. Address through a separately scoped dependency update and complete application checks.

## Rollback and review

Revert the PR to restore prior source behavior. Runtime changes retain inactive placements; undo operates only if its receipts still match and restored meetings pass validation. Reverting source does not automatically reverse data publications. No destructive migrations were added.

Automated code review and focused tests are technical evidence, not independent human approval. Merge, full CI acceptance, and production deployment remain pending.
