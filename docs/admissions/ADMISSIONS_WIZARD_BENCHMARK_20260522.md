# Admissions Wizard Benchmark (2026-05-22)

This brief compares Crown2026's current admissions wizard against leading school enrollment platforms and translates findings into mission-aligned action items.

## Crown2026 Current State (Live Walkthrough)

Walkthrough URL tested:
- http://127.0.0.1:5173/admissions/apply?

Flow tested end-to-end:
- Step 1 Interest
- Step 2 Inquiry
- Step 3 Family Profile
- Step 4 Student Profile
- Step 5 Mission Alignment
- Step 6 Documents
- Step 7 Review
- Step 8 Submit

What is working well:
- Clear 8-step structure with visible progress and checkpoint framing.
- Strong mission language appears in-step, not only as policy text.
- Required-field gating works at each stage.
- Save/resume messaging is present and reassuring.
- Family + student context supports household-level review.

Observed runtime issue:
- Final confirm produced HTTP 500 in this local run context.
- Browser surfaced plain-text 500 at submit time.
- Endpoint tested: POST /api/v1/admissions/submit/

Note:
- Focused backend tests for submit and admissions links were passing in code-level test runs, so this 500 is likely an environment/runtime wiring issue in local stack execution rather than a missing feature in the flow itself.

## Who Does It Right (and Why)

## 1) Blackbaud Enrollment Management

What they do well:
- Single family login across apply, status tracking, contracts, and re-enrollment.
- Personalized checklist and automated reminders.
- Self-scheduling for visits and events.
- Tight admissions-to-business-office continuity (contracts, deposits, tuition).

What Crown can learn:
- Add lifecycle continuity from application through contract and enrollment deposit with minimal context switching.
- Keep all family actions in one secure portal thread.

## 2) Finalsite Enrollment (SchoolAdmin)

What they do well:
- School-branded, polished first impression.
- Clear inquiry-to-enrollment flow with communication + checklist support.
- Waitlist/lottery support and strong operational analytics framing.

What Crown can learn:
- Improve visual trust signals and high-confidence onboarding polish at step boundaries.
- Add explicit waitlist/lottery and conversion-focused analytics views where applicable.

## 3) Veracross Admissions and Enrollment

What they do well:
- Family-first portal with status, events, letters, and deposits in one place.
- Strong file-review workflow for staff and candidate summary documents.
- Reporting and forecasting as a first-class admissions capability.

What Crown can learn:
- Elevate reviewer cockpit: candidate profile summaries, rubric snapshots, and decision evidence packet.
- Build real-time forecast widgets for funnel planning and staffing.

## 4) OpenApply

What they do well:
- Parent experience emphasizes quick apply/re-enroll, progress tracking, and timely updates.
- Broad ecosystem integration and internationalization posture.
- Workflow automation while keeping collaboration central.

What Crown can learn:
- Expand parent-facing progress visibility and proactive nudges.
- Strengthen integration strategy around payments, SIS, and communications.

## 5) Ravenna Hub

What they do well:
- Very clear family portal entry point and account-first continuity.
- Event registration and progress tracking in one place.
- Simple, trustworthy login and support surfaces.

What Crown can learn:
- Keep onboarding friction low with very clear account-state and support-state messaging.
- Make help and support discoverable at every step.

## Crown2026 Mission and Portrait Fit: Strategic Position

Crown already has a differentiator most vendors do not foreground:
- Explicit Christian mission and covenant language in the actual wizard experience.
- Portrait of the Graduate direction tied to admissions narrative.

This is a major strength if kept human-led and transparent.

Guardrails to preserve:
- Mission alignment should guide relational discernment, not become opaque auto-scoring.
- Portrait indicators should inform support and formation plans, not become exclusion logic.
- Decision records should require human rationale and auditable evidence.

## Recommended Priorities (Mission-Aligned)

## Priority 0: Submission Reliability

Goal:
- Zero-failure final submit experience.

Actions:
- Resolve local/stack runtime 500 path and add environment-level smoke check.
- Return structured error payloads to user with actionable next-step text.
- Add post-submit confirmation state that includes timeline and contact expectations.

## Priority 1: Family Trust and Clarity

Goal:
- Families should always know what is complete, what is next, and when they will hear back.

Actions:
- Add stage timeline with SLA promises (for example, first response in 1 business day).
- Add per-step completion chips that persist in review and dashboard states.
- Add explicit “what happens after submit” panel with expected milestones.

## Priority 2: Admissions Reviewer Excellence

Goal:
- Staff should be able to make faster, clearer, more humane decisions.

Actions:
- Build reviewer summary packet per household and per student.
- Show mission/portrait narrative summary with evidence notes.
- Add decision reason templates and consistency checks.

## Priority 3: Enrollment Conversion Continuity

Goal:
- Move from accepted to enrolled with fewer drop-offs.

Actions:
- Connect acceptance state to enrollment checklist and payment/deposit tasks.
- Add event scheduling and communication checkpoints in-family portal.
- Keep one-login continuity across admissions and enrollment operations.

## Suggested KPI Set (Operational + Mission)

Operational funnel KPIs:
- Inquiry to application start conversion
- Start to submitted conversion
- Submitted to decision time
- Accepted to enrolled conversion
- Stage aging and no-follow-up alerts

Mission-quality KPIs:
- Mission conversation completion rate
- Family partnership commitment completion rate
- Early-fit confidence pulse after enrollment (30/90 day)
- First-term retention by admissions cohort

## Bottom Line

Who does it right:
- Blackbaud, Finalsite, Veracross, OpenApply, and Ravenna each demonstrate high-value patterns in family UX continuity, checklist automation, communication, and reviewer operations.

What Crown2026 should keep and amplify:
- Mission and Christian values integrated directly in workflow.
- Portrait of the Graduate as formation-aligned, human-reviewed evidence.

What to finish next:
- Production-grade submission reliability, reviewer packet quality, and admissions-to-enrollment continuity in one family journey.
