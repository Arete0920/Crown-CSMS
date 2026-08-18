# CROWN Buyer Demo Walkthrough

**Status:** Current buyer-demo guide  
**Entry:** `/sandbox`  
**Demo school:** Heritage Christian Academy  
**Authentication model:** No buyer password. The public launcher creates a bounded role-scoped sandbox session before entering protected application routes.

## Presentation standard

Every walkthrough surface must use the approved CROWN visual language already loaded application-wide:

- `frontend/dashboards/src/styles/crown-theme.css` for semantic color, radius, shadow, and typography tokens;
- `frontend/dashboards/src/styles/launch-shell.css` for the canonical application layout and presentation system;
- `frontend/dashboards/src/styles/client-experience.css` for the buyer/client experience layer;
- `CrownLogo` and `CrownIcon` for brand and navigation identity;
- `CrownDashboardTemplate` and its metric, KPI, queue, alert, insight, quick-action, status, data-truth, and right-rail components wherever a dashboard/module command surface is used.

Do not create a second buyer-demo design system. New walkthrough pages and workflow surfaces must inherit the same spacing, hierarchy, semantic colors, KPI treatment, cards, widgets, alerts, tables, responsive behavior, and role-aware shell conventions.

## Buyer entry

1. Open `/sandbox`.
2. Select Guided path for the first walkthrough.
3. Select the desired role.
4. CROWN creates the protected Heritage demo session automatically.
5. Continue through the role journey below. Direct internal routes are valid only after that role-scoped sandbox session exists.

## School Administrator

Purpose: show the operating system for a whole school rather than a dashboard-only tour.

1. `/school-admin-dashboard` — leadership KPIs, priorities, alerts, and operational command modules.
2. `/registrar-dashboard` — student and enrollment record context.
3. `/attendance` — attendance workflow and exception handling.
4. `/gradebook` — academic and grading context.
5. `/finance` — financial operating picture without bypassing finance controls.
6. `/communications-dashboard` — school communication workflow.

Proof points: KPI hierarchy, queues, alerts/exceptions, connected records, role-aware navigation, data-truth labels, responsive cards/widgets.

## Admissions Director

1. `/admissions-dashboard` — pipeline operating picture.
2. `/admissions/pipeline` — applicant pipeline.
3. `/admissions/apply` — application workflow.
4. `/admissions/checklist` — checklist/document status.
5. `/enrollment-conversion` — accepted-to-enrolled conversion.

Proof points: inquiry-to-enrollment continuity, stage KPIs, next-action widgets, document/checklist state, conversion workflow.

## Finance Director

1. `/finance` — finance command surface and KPIs.
2. `/finance/invoices` — authoritative family invoices and balances.
3. `/finance/family-account` — family account and allocation history.
4. `/finance/exceptions` — payment/receivable exception workflow.
5. `/finance/bank-reconciliation` — reconciliation context.

Proof points: canonical finance ownership, penny-sensitive data treatment, exception workflow, auditability, payment-provider boundary remains fail closed.

## Teacher / Staff

1. `/teacher` — teacher workspace.
2. `/teacher/classes` — assigned classes and roster context.
3. `/teacher/attendance` — classroom attendance.
4. `/teacher/lesson-plans/today` — lesson planning and curriculum resource workflow.
5. `/teacher/daily-cockpit` — instructional priorities and assignments.
6. `/academics/teacher-grading` — authorized grading workflow.
7. `/gradebook` — resulting grade/progress context.

Proof points: daily workflow beyond dashboard presentation, lesson planning, curriculum connection, attendance, assignments, grading, role scope.

## Parent / Guardian

1. `/parent/admissions/start` — start/resume application.
2. `/admissions/apply` — applicant workflow.
3. `/parent/admissions/status` — status and next action, including enrollment handoff.
4. `/parent` — family workspace.
5. `/parent/learning-status` — learning/progress context.
6. `/parent/attendance` — attendance visibility.
7. `/parent/billing` — family billing stage.

Proof points: complete family lifecycle, no administrative authority leakage, clear next actions, consistent cards/status treatment.

## Student

1. `/student` — learner workspace.
2. `/student/today` — daily schedule and next actions.
3. `/student/assignments` — assignments and learning tasks.
4. `/academics/student-work` — submitted work/progress context.

Proof points: learner self-service, focused KPI/status presentation, protected administrative/finance boundaries.

## Visual consistency acceptance

For every buyer-visible route:

- use semantic CROWN tokens; do not introduce ad hoc competing brand colors;
- preserve the canonical crown-and-cross identity and descriptor;
- use the same page hierarchy, section rhythm, radii, shadows, typography, and spacing system;
- KPIs use the canonical metric-card treatment and consistent label/value/detail ordering;
- queues, alerts, quick actions, status panels, tables, right rails, and data-truth labels use existing CROWN components/patterns;
- buttons and links follow the current primary/secondary hierarchy;
- desktop, tablet, and mobile layouts remain usable without horizontal workflow loss;
- direct demo links must never bypass role authorization;
- no buyer credentials are embedded in documentation or URLs;
- demo data remains synthetic and Heritage-only.

## Machine-readable authority

`frontend/dashboards/src/sandbox/buyerWalkthrough.js` is the maintained buyer journey manifest. Contract tests must fail if the walkthrough regresses to a login route, loses workflow depth beyond dashboards, drops a required persona, or stops identifying the current CROWN design authority.
