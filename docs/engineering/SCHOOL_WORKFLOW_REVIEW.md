# School workflow review

Review baseline: `4cb6c66a60bcfe15e0dd227194ab8098e4cc8673`.
Decision owner: TC Megahan. The owner authorized current-source review and integration
of useful workflow practices. Source app names or counts are not completion evidence.

The review covered 4,992 tracked paths, 2,141 active backend Python files through syntax
and import inventory, and 845 frontend source files through structural inventory.
Detailed behavior inspection focused on the domains below. This is not a claim that
all repository behavior or deployed operation has been exercised.

The numbered review items correspond to the owner's retained 62-item external research
inventory. The repository records its own implementation decisions rather than copying
external interfaces, narration, branding, or proprietary implementation.

| Review items | Current owner and evidence | Disposition |
|---|---|---|
| 1, 3, 58 | `academics/family_views.py`, `experience_views.py`, `experience_access.py`; classroom family UI | Extend the existing family digest with child identity, effective deadlines, receipt state, filtering and truthful limits. See `FAMILY_WEEKLY_AGENDA.md`. Task-effort and mobile usability claims still require real user measurements. |
| 2, 4, 47 | Core canonical identity, documented households compatibility bridge, `ClassroomDisclosure`, guardian-household wizard | Preserve account and relationship authority. Classroom-specific restrictions exist; system-wide granular guardian rights and a consent-aware family directory are not established by this review. |
| 5, 6 | Medical-related test files and restricted-data architecture | Nurse visits, medication administration, consent, and immunization workflows are not verified. Inspected medical API tests exercise generic health/authentication endpoints. Design any added health records around canonical student identity and dedicated permissions in a separate outcome. |
| 7, 40 | `academics/support_views.py`, `support_models.py`, `instruction_models.py`, canonical discipline/intervention links | Existing reviewed support, restorative follow-through and private deadline reasons are reusable. Comprehensive IEP/504 document lifecycle and nurse access require separate evidence. |
| 8, 9, 10, 38, 56 | Classroom records, published assignments, `comms/`, family notices/preferences | Existing scoped communications and dated work are reusable. A general calendar publication service and grade-alert transport require distinct proofs; provider acceptance is not delivery. |
| 11, 12, 62 | `academics/operations_views.py`, attendance audit/session models, classroom absence-explanation records | Attendance and guardian explanations exist. Verify the explanation-to-official-attendance review path before advertising automatic reconciliation. Do not replace audited attendance with a new parent writer. |
| 13, 16, 17, 18, 59, 61 | `aftercare/`, `billing/`, `ledger/`, payments hold; optional registration flows | Extended-care attendance, pickup authority and billing already have owners. Preserve payment containment. Single sign-on is not ledger synchronization; elective interest is not enrollment or a charge. Academic-record holds are not automatically adopted. |
| 14, 15 | `applications/` models/services, admissions identity conversion, checklist documents | Existing applications and verified student identity conversion are reusable. Document availability after acceptance and duplicate reconciliation need scenario-specific proof; model presence does not certify continuity. |
| 19, 33, 34, 35, 37 | School implementation runbook, onboarding wizards, in-app digest/conference tasks | Reuse school setup and notification infrastructure. Add measured role-specific training and milestone guidance in a separate workflow; hosted periodic execution remains environment-specific. |
| 20, 22, 23, 24, 41, 42, 43, 45, 51, 52, 53, 54 | Academic transcript access/issuance, grade evidence, leadership aggregates, existing report surfaces | Preserve official-output authority and audited corrections. Reusable progress/transcript profiles, historical imports and district reports need their own contract checks; preview grades are not report-card authority. Adapt reporting to actual school requirements. |
| 21 | `servicehours/`, formation and service responses | Preserve service-hour ownership and approval semantics. Verify distinct student and household obligations before expanding aggregate reports. |
| 25, 26, 27, 55, 57 | Academic terms/sections, scheduling/section-scheduler and promotion wizards; scheduling disposition records | Existing canonical scheduling, publication and year-transition paths are reusable. Verify conflict cases, future drafts, rotating patterns and promotion exceptions; do not introduce a competing timetable. |
| 28, 36, 39, 46 | Integration boundary and existing connector surfaces | Each integration needs supported objects, direction, identity mapping, retry and reconciliation evidence. App counts and externally advertised click comparisons are not certification. |
| 29, 30, 31, 32 | Assignment publishing/copying, lesson execution, curriculum links, submission revisions, grade evidence | Reuse existing instruction workflows. Preserve missing/unscored/zero distinctions and provisional versus official grade authority. Individual deadlines must be consistent in each family surface. |
| 44 | Canonical `core.Staff`, staff onboarding/setup; `hr.Employee` compatibility concerns | Structured staff requirements, expiry dates, completion evidence and escalation are not implemented by the inspected HR placeholder service. Establish canonical staff ownership before adding this separate domain outcome. |
| 48, 49, 50, 60 | Student import wizard, identity bridge rules, existing exports and frontend internationalization surfaces | Import preview exists; complete field/relationship reconciliation and recoverable export packages are not certified. Browser translation does not establish native localization of critical forms. |

## Integration order

1. Repair the existing family agenda, with scoped tests and explicit list limits.
2. Exercise admissions document continuity, absence review, care billing and scheduling
   scenarios against the authoritative source; create changes only for reproducible gaps.
3. Establish separately reviewable health and staff-requirement contracts with canonical
   ownership and access controls before introducing new persistence.
4. Verify report profiles, migration/export completeness and actual integration depth.
5. Produce role-specific training from checked workflows and realistic synthetic data.

Each outcome follows unchanged PR hygiene, tenant/access, schema, security and exact-head
release checks. Payment activation, deployment, live provider delivery and native Windows
execution are separate evidence boundaries. No unrelated open PR is modified by this review.
