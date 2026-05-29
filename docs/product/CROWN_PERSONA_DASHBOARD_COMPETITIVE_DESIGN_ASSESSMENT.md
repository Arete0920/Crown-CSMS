# CROWN Persona Dashboard Competitive Design Assessment

This document is an internal design/implementation guide.

It is based on the current CROWN dashboard architecture and prior competitor/persona research synthesis.

It does not claim final external market proof unless separately refreshed and cited.

It prioritizes consistency with the existing shared dashboard shell.

## 1. Current CROWN Dashboard Architecture Summary

CROWN is currently structured around one shared dashboard template pattern, not disconnected persona implementations.

Core architecture already present and required to preserve:
- Shared dashboard frame and visual shell through the template layer.
- Universal faith/community strip on persona pages (devotion, prayer list, announcements, celebrations).
- Universal communications strip on persona pages.
- Universal page-level source/sync/data truth surface.
- Generic `BASE_NOTE` containment so production pages do not render generic sandbox wording.
- Persona-specific metric and workflow content configured by template data.

Design implication:
- The platform should continue evolving through template-driven hierarchy and role tuning, not persona-by-persona structural forks.

## 2. Top 25 Competitor Comparison Matrix

| Competitor | Persona/page pattern | What it tends to show | KPI pattern | Visual/UX pattern | CROWN strong | CROWN weak | CROWN superior opportunity |
|---|---|---|---|---|---|---|---|
| Blackbaud Education Management | Enterprise role portals | Admissions, academics, billing, advancement | Executive + operational rollups | Mature, dense, trust-first | Unified mission + operations spine | Less mature visual hierarchy | Mission-rich private-school command center with cleaner action-first design |
| FACTS SIS / Family Portal | Family-action centered pages | Payments, forms, alerts, messages | Family required actions + balances | Practical, clear, parent-focused | Shared platform consistency + mission layer | Family mobile compression still uneven | Best-in-class Christian family operating hub |
| Veracross | Unified private-school records pages | Schoolwide lifecycle operations | Data integrity + institutional stats | Premium conservative enterprise | Cross-role shared shell strategy | Needs stronger trust signal density | Premium trust with clearer “what now” guidance |
| Alma | SIS analytics role dashboards | Attendance, academics, interventions | Decision and trend cards | Modern, concise, data-forward | Better mission and journey continuity | Not yet as polished in visual rhythm | Human-centered executive + academic command blend |
| Edsby | Classroom + engagement pages | Teacher/student learning engagement | Completion and participation | Clean educational UX | Broader all-school operating scope | Teacher day-flow still less optimized | Teacher experience that ties directly to school operations |
| Finalsite | Comms and enrollment experience pages | Websites, campaigns, admissions paths | Conversion + engagement | Highly polished marketing UX | Stronger operations backbone | Surface polish inconsistent by persona | Premium polish with operational depth |
| SchoolAdmin-style enrollment platforms | Funnel-driven admissions pages | Inquiry, checklist, decision stages | Funnel movement + conversion | Wizard-centric, low-friction | End-to-end lifecycle continuity | Admissions microinteractions can improve | Best admissions-to-enrollment continuity with shared shell |
| TADS | Tuition/admissions/admin pages | Billing, aid, enrollment administration | Fees, aid queues, aging | Functional, conservative | Stronger template architecture | Finance hierarchy still improving | Finance clarity + mission context in one system |
| PowerSchool | Large SIS operations pages | Records, attendance, gradebook, reports | Institutional operations KPI sets | Utility-first, often dense | More coherent role shell direction | Fewer mature enterprise cues | Cleaner and easier private-school alternative |
| Infinite Campus | District-grade SIS pages | Operations, attendance, records | Operational throughput + compliance | Data-heavy utility design | Christian/private-school relevance | Not as broad in institutional controls | Better ease-of-use for private/Christian contexts |
| Skyward | Legacy SIS role pages | Admin-heavy records and workflows | Back-office operational counts | Traditional, lower modern polish | Strong shared modern shell | Needs further readability tuning | Clear visual modern upgrade path |
| Rediker | Traditional school admin pages | Core SIS modules | Administrative completion metrics | Practical, less contemporary | Better mission and shell consistency | Needs stronger consistency in hierarchy | Higher polish with same administrative reliability |
| Gradelink | Lightweight SIS role pages | Grades, attendance, communication | Essential daily KPIs | Simple and approachable | Better architectural extensibility | Must maintain simplicity while scaling | Simple-first UX with richer decision context |
| Sycamore Education | Christian/private-school familiar pages | Family, academics, communication | Core private-school KPI basics | Familiar but mixed polish | Shared Christian-school identity depth | Needs broader polish consistency | Most attractive Christian-school-native experience |
| Jupiter Ed | Teacher-centric workflow pages | Gradebook and class operations | Assignment + grading KPIs | Fast teacher utility | Whole-school cross-role integration | Teacher flow can be further compressed | Teacher velocity plus governance continuity |
| SchoolCues | Family communications pages | Parent alerts, fees, school notices | Family engagement and payment KPIs | Parent practical | Shared dashboard strategy across all roles | Parent-first action stack still maturing | Family clarity equal to specialists plus full operations |
| OpenApply | Admissions-centric pages | Inquiry to decision and document flow | Funnel velocity and stage conversion | Polished admissions flow | Lifecycle continuity to enrollment/ops | Admissions-specific hierarchy can improve | Seamless admissions + onboarding + SIS continuity |
| iSAMS | Independent-school ops pages | Institutional admin + academics | Institutional completion and readiness | Professional institutional tone | Mission + communication + truth layers | Needs stronger board-ready summary mode | Better leadership narrative with less clutter |
| Engage | Parent/community portal pages | Comms, attendance, parent services | Engagement and response KPIs | Accessible and practical | Richer role-specific dashboard map | Needs mobile and readability hardening | Unified role depth with equal usability |
| ManageBac | Program/curriculum pages | Curriculum and learner progress | Program compliance + learner progress | Modern, curriculum-strong | Broader operations and mission context | Curriculum persona polish can increase | Curriculum + operations + mission in one frame |
| ParentSquare | Communication-focused pages | Messaging, alerts, audience targeting | Open/reply/alert metrics | Clear communication UX | Universal communications strip architecture | Still refining role-specific comms hierarchy | Communications quality at specialist level in full platform |
| Brightwheel | Family/day operations pages | Family updates, payments, daily flow | Parent action and timeliness KPIs | Mobile-first, highly approachable | Wider K-12/private scope | Mobile compression for family/student ongoing | Mobile-first clarity with deeper school operations |
| Toddle | Learning experience pages | Classroom evidence and portfolios | Learning progression KPIs | Elegant, student-centered | Stronger mission and operations breadth | Student persona delight can improve | Delight + operational reliability blend |
| RenWeb legacy pattern | Legacy private-school portals | Family/admin transactional pages | Basic transactional KPIs | Familiar but dated | Modern shell and trust-state potential | Needs consistent premium finish | Clear migration path from legacy private-school UX |
| Niche private/Christian portals and utilities | Point-solution utility pages | One-function workflows | Narrow KPIs by module | Functional, fragmented | Unified architecture + mission identity | Must avoid equal-weight clutter | One coherent Christian-school operating system |

## 3. Where CROWN Is Strong

- Shared shell architecture enables consistency and lower long-term UX drift.
- Universal faith/community layer gives authentic Christian-school differentiation.
- Universal communications layer supports cross-role continuity.
- Universal source/sync truth surface improves production credibility.
- Role-aware dashboards and routes support persona-specific behavior without forking the platform.

## 4. Where CROWN Is Weak

- Some persona pages still carry equal-weight card density that dilutes decision priority.
- School Administrator hierarchy is only in first pass and needs polish iterations.
- Parent/family and student mobile compression still needs deeper execution.
- Teacher task-first sequencing can be tightened to reduce cognitive load.
- Accessibility and contrast cleanup remains an explicit remaining tranche.

## 5. Where CROWN Can Become Superior

- Combine enterprise-grade operational command with mission-centered identity.
- Make role pages answer one top question immediately, then progressive depth.
- Keep all personas inside one shell while tailoring KPI order and workflow widgets.
- Make truth-state and communications visible and actionable across every role.
- Out-discipline competitors with fewer equal-weight cards and clearer action flow.

## 6. Persona-By-Persona Dashboard/Page Expectations

### School Administrator / Head of School
- Primary question the page must answer: What leadership decisions require same-day action?
- Top KPIs: decisions needed, enrollment, attendance completion, AR risk, staff coverage, safety/student care.
- Required widgets: decision panel, priorities queue, exceptions panel, cross-department readiness table.
- Useful wizards: escalation triage, approvals bundle, cross-department action plan wizard.
- Useful automations: approval reminders, exception escalation, unresolved queue digests.
- Visual style expectation: executive calm, clear urgency coding, strong first-screen hierarchy.

### Teacher
- Primary question the page must answer: What classroom actions are due now for student success?
- Top KPIs: classes today, attendance due, grading backlog, at-risk students, parent replies.
- Required widgets: class action queue, grading queue, intervention watchlist, communications snippets.
- Useful wizards: attendance correction, grading completion, intervention note workflow.
- Useful automations: missing-grade alerts, attendance reminders, guardian outreach prompts.
- Visual style expectation: quick-scan, low-friction, action-first.

### Parent / Family
- Primary question the page must answer: What does my family need to complete today?
- Top KPIs: action-required count, balance due, forms due, attendance exceptions, unread messages.
- Required widgets: family action center, billing status, forms checklist, child highlights.
- Useful wizards: payment plan setup, form completion, reenrollment journey.
- Useful automations: due reminders, payment nudges, incomplete form alerts.
- Visual style expectation: mobile-first, reassuring, high readability.

### Student
- Primary question the page must answer: What should I complete next to stay on track?
- Top KPIs: assignments due, missing work, current average, attendance, upcoming events.
- Required widgets: today’s agenda, due work list, class progress, encouragement panel.
- Useful wizards: schedule planner, assignment submission helper, goal check-in.
- Useful automations: due reminders, missing work nudges, intervention prompts.
- Visual style expectation: focused, motivating, uncluttered.

### Admissions
- Primary question the page must answer: What moves families from inquiry to enrollment today?
- Top KPIs: new inquiries, submitted applications, pending decisions, conversion risk, SLA breaches.
- Required widgets: funnel stage board, missing-document queue, communications queue, conversion blockers.
- Useful wizards: packet completion, decision workflow, handoff to enrollment.
- Useful automations: stage reminders, missing item follow-ups, decision SLA alerts.
- Visual style expectation: pipeline clarity, stage-forward progression.

### Finance / Business Office
- Primary question the page must answer: Which financial exceptions need action now?
- Top KPIs: AR risk, overdue accounts, aid queue, payment failures, reconciliation delta.
- Required widgets: exception queue, risk segments, plan status board, aid approvals.
- Useful wizards: payment outreach sequence, adjustment approvals, aid decision flow.
- Useful automations: overdue escalations, payment failure retries, aid reminders.
- Visual style expectation: exception-first, precise, audit-friendly.

### Board / Executive
- Primary question the page must answer: Is the school healthy, mission-aligned, and on plan?
- Top KPIs: enrollment trend, retention, tuition health, risk posture, mission outcomes.
- Required widgets: board packet summary, strategic trends, critical risks, mission highlights.
- Useful wizards: board packet generation, strategic scenario review.
- Useful automations: pre-board digest, threshold alerts, monthly strategic summary.
- Visual style expectation: concise strategic summary, low noise.

### Communications
- Primary question the page must answer: What communications require response or publication now?
- Top KPIs: unread queues, response SLA, announcement backlog, urgent alerts.
- Required widgets: inbox queue, announcement scheduler, audience targeting panel, urgent alerts.
- Useful wizards: campaign composer, audience selector, emergency alert workflow.
- Useful automations: SLA nudges, scheduled sends, unacknowledged alert escalation.
- Visual style expectation: queue clarity, message confidence, low friction.

### Spiritual Life / Mission
- Primary question the page must answer: How are mission rhythms and spiritual care progressing?
- Top KPIs: prayer follow-ups, chapel participation, service hours, discipleship actions.
- Required widgets: mission rhythm board, prayer follow-up queue, celebration stream.
- Useful wizards: prayer request routing, service-hour validation, mission event planning.
- Useful automations: follow-up reminders, chapel prep prompts, milestone celebrations.
- Visual style expectation: reverent, warm, calm, action-capable.

### Health / Safety / Counseling
- Primary question the page must answer: Which care and safety issues need immediate response?
- Top KPIs: incidents open, counseling queue, unresolved health forms, high-priority cases.
- Required widgets: incident queue, care follow-up tracker, compliance checklist.
- Useful wizards: incident triage, care plan update, parent contact flow.
- Useful automations: unresolved incident alerts, care follow-up reminders.
- Visual style expectation: discreet urgency, clarity, privacy-respecting structure.

### Registrar
- Primary question the page must answer: What records or scheduling accuracy issues need correction?
- Top KPIs: records pending, schedule conflicts, transcript queue, enrollment transitions.
- Required widgets: record completion board, conflict queue, transcript pipeline.
- Useful wizards: transcript workflow, records correction workflow.
- Useful automations: missing-record reminders, conflict escalation.
- Visual style expectation: precision-first, low ambiguity.

### HR
- Primary question the page must answer: Which staffing and compliance tasks are critical today?
- Top KPIs: coverage gaps, onboarding tasks, expiring credentials, open HR actions.
- Required widgets: coverage queue, credential tracker, hiring pipeline summary.
- Useful wizards: onboarding flow, substitute assignment flow.
- Useful automations: credential expiry reminders, coverage escalation.
- Visual style expectation: operational clarity, people-first details.

### Facilities
- Primary question the page must answer: What facility issues affect today’s readiness?
- Top KPIs: open work orders, critical repairs, inspections due, readiness score.
- Required widgets: work-order queue, inspections board, critical systems status.
- Useful wizards: maintenance dispatch, inspection completion.
- Useful automations: overdue work-order alerts, inspection reminders.
- Visual style expectation: practical, status-forward.

### Transportation
- Primary question the page must answer: Are routes and rider safety ready for today?
- Top KPIs: route readiness, unresolved incidents, staffing coverage, delays.
- Required widgets: route board, exception queue, communications to families.
- Useful wizards: route adjustment, incident intake.
- Useful automations: delay notifications, route exception alerts.
- Visual style expectation: schedule clarity, safety emphasis.

### Food Service
- Primary question the page must answer: Are nutrition services and compliance on track today?
- Top KPIs: meal counts, allergy exceptions, inventory risks, service delays.
- Required widgets: service readiness board, allergy queue, inventory tracker.
- Useful wizards: menu update, allergy override approval.
- Useful automations: low-stock warnings, allergy alert reminders.
- Visual style expectation: clear, practical, low clutter.

### IT
- Primary question the page must answer: What system reliability issues need immediate action?
- Top KPIs: failed syncs, open incidents, uptime status, backup health.
- Required widgets: incident queue, integration health panel, reliability trend panel.
- Useful wizards: incident triage, sync recovery workflow.
- Useful automations: outage alerts, retry escalations, unresolved incident digests.
- Visual style expectation: technical clarity with non-technical readability.

### Athletics
- Primary question the page must answer: What athletic operations or student obligations need action?
- Top KPIs: eligibility exceptions, schedule conflicts, transport readiness, staffing gaps.
- Required widgets: event operations queue, eligibility tracker, coach communications.
- Useful wizards: event readiness, roster/eligibility updates.
- Useful automations: eligibility reminders, event alerts.
- Visual style expectation: energetic but controlled.

### Advancement
- Primary question the page must answer: Which fundraising and relationship actions drive outcomes now?
- Top KPIs: donor pipeline, campaign progress, pledge follow-up, event conversion.
- Required widgets: donor action queue, campaign timeline, outreach status.
- Useful wizards: donor outreach planner, campaign launch checklist.
- Useful automations: pledge follow-up reminders, campaign milestone notices.
- Visual style expectation: premium, relationship-centered, actionable.

### Library / Media
- Primary question the page must answer: What circulation and media support tasks are due?
- Top KPIs: overdue assets, media requests, support queue, resource availability.
- Required widgets: circulation queue, media support board, request tracker.
- Useful wizards: acquisition request workflow, overdue resolution flow.
- Useful automations: overdue notices, request SLA reminders.
- Visual style expectation: orderly, learning-support focused.

### Extended Care
- Primary question the page must answer: Are extended care operations and family communications current?
- Top KPIs: attendance variance, pickup exceptions, staffing readiness, billing exceptions.
- Required widgets: care roster queue, pickup alerts, family updates.
- Useful wizards: enrollment update, pickup authorization flow.
- Useful automations: pickup alerts, attendance exception reminders.
- Visual style expectation: family-safe and operationally clear.

### Academic Support / Student Services
- Primary question the page must answer: Which support plans and interventions need immediate follow-through?
- Top KPIs: active support plans, overdue follow-ups, intervention outcomes, high-priority students.
- Required widgets: intervention queue, plan compliance tracker, counselor collaboration board.
- Useful wizards: support-plan update, intervention referral flow.
- Useful automations: overdue intervention reminders, plan milestone prompts.
- Visual style expectation: supportive, clear, and confidentiality-aware.

Universal requirement for every persona page:
- Faith/community layer is always present.
- Communications layer is always present.
- Page-level data truth/source/sync status is always present.

## 7. Persona KPI Recommendations

Cross-persona KPI rules:
- Keep top-row KPI count tight (4-6 depending on role breadth).
- Put decision/exception KPIs first for operational roles.
- Pair KPI value with one explicit action implication.
- Avoid KPI duplication between first-row and below-fold cards.
- Standardize terminology for readability and trust.

Role-specific KPI emphasis:
- School Administrator: decisions needed, enrollment, attendance completion, AR risk, staff coverage, safety/care.
- Teacher: classes today, grading backlog, attendance due, at-risk students, parent replies.
- Parent/Family: actions due, balance due, forms due, messages unread, attendance exceptions.
- Student: assignments due, missing work, current average, attendance, upcoming events.
- Admissions: inquiry velocity, submitted apps, decision SLA, conversion risk.
- Finance: AR risk, payment failures, aid queue, reconciliation exceptions.
- Board/Executive: strategic trends, risk posture, mission outcomes.

## 8. Persona Widgets/Wizards/Automations Recommendations

Widget strategy:
- One consistent widget grammar across personas: KPI card, queue card, status card, trend card, feed card, action card.
- Persona pages differ by queue content and action intent, not component architecture.

Wizard strategy:
- Keep wizards short, progressive, and role-specific.
- Expose completion state and next handoff clearly.

Automation strategy:
- Prioritize reminders and escalation on unresolved queues.
- Tie automations directly to KPI exceptions and SLA breaches.

## 9. 50 Prioritized Improvements

### Universal visual system
1. Standardize first-screen priority structure across personas.
2. Limit first-row metrics to role-critical signals only.
3. Reduce equal-weight card density on busy pages.
4. Enforce consistent spacing and rhythm in all cards.
5. Tighten typographic hierarchy for scannability.
6. Normalize status tone usage across cards.
7. Standardize card border and elevation intensity.
8. Keep shared strips fixed in relative order on every persona.
9. Keep page-level truth-state above role metrics.
10. Ensure no production persona renders generic sandbox copy.

### School Administrator first
11. Keep decision panel above metric grid for leadership pages.
12. Preserve decision-first metric ordering in first six cards.
13. Add explicit urgency tags to pending approvals.
14. Reduce duplicate urgency language between decision panel and priorities list.
15. Make department readiness table exception-highlighting clearer.
16. Tighten copy in alerts to action+owner format.
17. Add clearer same-day cutoff language for critical queues.
18. Ensure first-screen presents decisions, not aggregate totals.
19. Keep right-rail cards aligned to decision panel actions.
20. Add small visual distinction between watch vs stable states.

### Teacher
21. Reorder teacher metrics to class actions first.
22. Bring grading backlog and attendance due into first-row emphasis.
23. Group intervention tasks by urgency.
24. Add direct links from at-risk indicators to intervention workflow.
25. Reduce non-actionable decorative content in first screen.

### Parent / Family
26. Prioritize action-required counts above general summaries.
27. Improve mobile compression for family cards and strips.
28. Surface forms/payments/messaging in one family action stack.
29. Clarify due dates and consequences in family tasks.
30. Keep child-context switching visible and simple.

### Student
31. Put due work and missing work at top of student page.
32. Keep student language plain, encouraging, and concise.
33. Add quick next-action affordances for assignments.
34. Reduce analytics-heavy widgets on first student screen.
35. Maintain faith/community and communications presence without clutter.

### Admissions / Finance / Board
36. Admissions: strengthen funnel stage transitions and blockers panel.
37. Admissions: improve checklist completeness visibility.
38. Finance: lead with exception queues over aggregate totals.
39. Finance: highlight AR risk cohorts and pending approvals.
40. Board: implement concise board-packet summary mode.
41. Board: elevate strategic trends over operational noise.
42. Board: show mission outcomes with operational context.

### Mission / Safety / Support
43. Spiritual life: tie mission widgets to follow-up action queues.
44. Safety/counseling: emphasize high-priority unresolved cases.
45. Student support: make intervention follow-through deadlines explicit.
46. Health/safety: improve readability for urgent status states.

### Certification / accessibility
47. Keep persona certification test as required gate in focused validation.
48. Add accessibility checks for contrast and heading order in shared shell.
49. Add tests for mobile class behavior on critical strip/grid containers.
50. Add snapshot or semantic checks for truth-state and communications in each persona run.

## 10. Codebase-Aligned Implementation Order

1. Keep shared shell and universal strips stable (no architecture fork).
2. Maintain persona certification as a mandatory gate for all production personas.
3. Complete School Administrator hierarchy polish in iterative passes.
4. Apply parent/family mobile compression improvements.
5. Apply teacher task-first hierarchy pass.
6. Apply finance exception-first hierarchy pass.
7. Apply admissions funnel clarity and checklist conversion polish.
8. Implement board packet mode and executive narrative clarity.
9. Expand persona KPI/order refinements role by role.
10. Run accessibility/contrast cleanup and enforce through focused dashboard validation.
