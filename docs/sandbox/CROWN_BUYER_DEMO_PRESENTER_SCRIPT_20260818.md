# CROWN Buyer Demo Presenter Script

**Status:** Team-use walkthrough script  
**Entry URL:** `/sandbox` on the currently verified sandbox host  
**Demo school:** Heritage Christian Academy  
**Authentication:** No buyer password. CROWN creates a bounded role-scoped sandbox session before protected routes open.  
**Companion route authority:** `docs/sandbox/CROWN_BUYER_DEMO_WALKTHROUGH_20260818.md`

## Presenter standard

Use this script until the team can deliver the walkthrough comfortably without prompts. Do not improvise alternate URLs, credentials, claims, or unsupported production statements.

Keep the visual story consistent throughout the demo. Call attention to the same CROWN hierarchy on every surface: title/decision context, KPI cards, priorities/queues, alerts, widgets, quick actions, data-truth labels, role navigation, and detailed workflow pages. The demo should feel like one platform, not separate modules stitched together.

## Recommended 30-minute sequence

### 0. Opening — 2 minutes

**Say:**

“CROWN is a production-ready Christian School Management Solution built as one connected operating platform. This demonstration uses Heritage Christian Academy, a protected synthetic-data school. You will not need a username or password. We will enter through the buyer sandbox, choose a role, and then move through the same role-aware workspace and workflows a school uses.”

**Show:**

1. Open `/sandbox`.
2. Point out `Demo data only`, `No buyer password`, and `Real role workspace`.
3. Select **Guided path**.
4. Explain that changing roles creates a new bounded role-scoped sandbox session rather than bypassing authorization.

**Do not say:**

- that the successor production environment is already deployed or accepted;
- that payment processing is active;
- that CROWN has third-party legal/regulatory certification that has not been independently established.

---

### 1. School Administrator — 6 minutes

**Launch:** School Administrator.

**Narrative:**

“This is the leadership operating picture. CROWN is designed to move from executive visibility into the underlying work without changing systems.”

**Route sequence and talking points:**

1. `/school-admin-dashboard`
   - Show leadership KPIs, priorities, alerts, department/command widgets, quick actions, and data-truth indicators.
   - Point out the consistent CROWN layout and visual hierarchy.
2. `/registrar-dashboard`
   - Show student/enrollment record context and how administrative operations connect to student records.
3. `/attendance`
   - Show attendance workflow and exception handling rather than only the attendance dashboard.
4. `/gradebook`
   - Show academic/grading context and role-scoped access.
5. `/finance`
   - Show financial operating picture, exceptions, and controls.
6. `/communications-dashboard`
   - Show the communication operating surface and connection back to school operations.

**Transition:**

“Now that you have seen the school-wide view, we will follow the same platform through the family acquisition lifecycle.”

---

### 2. Admissions Director — 4 minutes

**Return to `/sandbox` and launch:** Admissions Director.

**Say:**

“Admissions is not a static pipeline. The walkthrough follows a fictional family from inquiry through application, checklist, decision, and enrollment conversion.”

**Route sequence:**

1. `/admissions-dashboard` — pipeline KPIs and next actions.
2. `/admissions/pipeline` — live applicant workflow.
3. `/admissions/apply` — application process.
4. `/admissions/checklist` — document/checklist state.
5. `/enrollment-conversion` — accepted-to-enrolled handoff.

**Emphasize:** continuity of records, next actions, stage visibility, and consistent CROWN cards/widgets.

---

### 3. Finance Director — 4 minutes

**Return to `/sandbox` and launch:** Finance Director.

**Say:**

“Finance is built around authoritative balances, traceable transactions, exceptions, and reconciliation. The payment-provider boundary remains intentionally fail closed until the contracted provider is activated and certified.”

**Route sequence:**

1. `/finance` — KPIs and operating picture.
2. `/finance/invoices` — authoritative family invoices/balances.
3. `/finance/family-account` — account and allocation history.
4. `/finance/exceptions` — exception workflow.
5. `/finance/bank-reconciliation` — reconciliation context.

**Emphasize:** penny-sensitive treatment, auditability, workflow continuity, and the deliberate payment-provider control boundary.

---

### 4. Teacher / Staff — 5 minutes

**Return to `/sandbox` and launch:** Teacher / Staff.

**Say:**

“The teacher experience is a working day, not a dashboard tour.”

**Route sequence:**

1. `/teacher` — teacher workspace.
2. `/teacher/classes` — assigned classes/roster.
3. `/teacher/attendance` — classroom attendance.
4. `/teacher/lesson-plans/today` — create/edit lesson plans and connect curriculum resources.
5. `/teacher/daily-cockpit` — instructional priorities and assignments.
6. `/academics/teacher-grading` — authorized grading workflow.
7. `/gradebook` — resulting grade/progress context.

**Emphasize:** role scope, instructional flow, persisted work, and consistency of the shell/KPI/action hierarchy.

---

### 5. Parent / Guardian — 5 minutes

**Return to `/sandbox` and launch:** Parent / Guardian.

**Say:**

“The family experience begins before enrollment and continues through the everyday school relationship.”

**Route sequence:**

1. `/parent/admissions/start` — start/resume application.
2. `/admissions/apply` — applicant workflow.
3. `/parent/admissions/status` — status, next action, and enrollment handoff.
4. `/parent` — family workspace.
5. `/parent/learning-status` — academic/progress context.
6. `/parent/attendance` — attendance visibility.
7. `/parent/billing` — billing stage and family finance context.

**Emphasize:** one lifecycle, clear next actions, no administrative authority leakage, and the same visual language used throughout CROWN.

---

### 6. Student — 2 minutes

**Return to `/sandbox` and launch:** Student.

**Say:**

“The student sees a focused learner workspace rather than administrative complexity.”

**Route sequence:**

1. `/student` — learner workspace.
2. `/student/today` — schedule/next actions.
3. `/student/assignments` — assignments and learning tasks.
4. `/academics/student-work` — submitted work/progress context.

**Emphasize:** simplicity, role boundaries, and no access to administrative/finance controls.

---

### 7. Close — 2 minutes

**Say:**

“What you have seen is one role-aware platform using the same CROWN design system and the same connected records across leadership, admissions, finance, classroom, family, and student workflows. The product and repository are production-ready. Buyer-specific deployment, account transfer, monitoring ownership, operational acceptance, and payment-provider activation are controlled transaction-time activities after the applicable agreements are executed.”

Invite questions around workflow, implementation, transition, support, data migration, integrations, or ownership handoff.

## Presenter recovery rules

If a route does not load correctly during rehearsal:

1. Do not improvise a different undocumented URL.
2. Record the exact role, route, time, and visible error.
3. Return to `/sandbox` and relaunch the intended role.
4. If it repeats, stop using that route until browser authority is repaired and rerun.

If the sandbox redirects to `/login`, `/not-authorized`, or `/forbidden` on an intended journey route, treat it as a demo-blocking failure for that route rather than working around authorization.

If data is unavailable, do not represent fallback/sample records as live production data. Use the CROWN data-truth indicator exactly as displayed.

## Team rehearsal cadence

Until the team is comfortable:

- run the browser-authority command before a material buyer demo or after any sandbox/navigation change;
- rehearse this exact sequence at least once with the person presenting;
- use Guided mode for buyer presentations;
- keep one team member available to record defects rather than debugging live in front of the buyer;
- revise this script only when the canonical buyer walkthrough manifest changes.

## Browser-authority command

From `frontend/dashboards` with dependencies installed:

**PowerShell:**

```powershell
$env:CROWN_LIVE_FRONTEND_URL = "https://<current-sandbox-host>"
npm run certify:buyer-sandbox-browser
```

**Headed rehearsal mode:**

```powershell
$env:CROWN_LIVE_FRONTEND_URL = "https://<current-sandbox-host>"
$env:CROWN_DEMO_HEADED = "1"
npm run certify:buyer-sandbox-browser
```

The browser authority records `/build.json`, traverses every maintained buyer route, captures screenshots, and writes `test-results/buyer-sandbox-browser-authority.json`.
