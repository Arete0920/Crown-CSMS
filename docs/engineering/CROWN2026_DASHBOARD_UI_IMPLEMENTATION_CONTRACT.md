CROWN2026 DASHBOARD / WIZARD / WIDGET / STYLING IMPLEMENTATION CONTRACT
LOCKED WORKING BASELINE
Date: 2026-03-10
Status at handoff:
- Dashboard normalization contract locally satisfied
- 6 PASS
- 4 PASS_WITH_DRIFT
- 0 FAIL
- Remaining work is governance drift cleanup, UI consistency, wizard consistency, widget consistency, and production polish
- This is NOT a green light for random new pages or route invention

==================================================
A. PRIMARY OBJECTIVE
==================================================

Finish the Crown frontend experience so it feels like one coherent product, not a pile of pages.

This means:
1. Canonical dashboard routing must remain stable
2. Navigation must point to the correct primary surfaces
3. Workspace routes must remain secondary/specialized where intended
4. Dashboards, widgets, cards, and wizards must share one design system
5. UI must look operational, polished, role-aware, and demo-ready
6. No new chaos, no route sprawl, no duplicate concepts with different names

==================================================
B. NON-NEGOTIABLE RULES
==================================================

1. Do not invent new route names unless explicitly approved
2. Do not create duplicate dashboards for concepts that already exist
3. Do not promote workspace routes to primary nav unless approved
4. Do not break legacy alias support already intentionally retained
5. Do not widen Reporting / Summary into a standalone surface in this pass
6. Do not mix unrelated dirty repo work into dashboard normalization commits
7. Do not ship inconsistent styling between dashboard families
8. Do not let "exists in files" be confused with "is wired and usable"
9. Every dashboard surface must have:
   - page
   - route
   - nav or entry point
   - consistent shell/layout
   - realistic widgets/cards/tables
10. Every wizard must have:
   - clear steps
   - clear progress
   - save/back/next behavior
   - success state
   - clean validation messaging
   - consistent visual language

==================================================
C. CURRENT ROUTING / NAV CONTRACT (LOCKED)
==================================================

Priority dashboard surfaces and canonical routes:

1. Billing
   - Canonical route: /billing-dashboard
   - Allowed legacy alias: /billing
   - Primary nav target: /billing-dashboard
   - Status: PASS

2. Financial Aid
   - Canonical route: /financial-aid-dashboard
   - Allowed legacy alias: /financial-aid
   - Primary nav target: /financial-aid-dashboard
   - Status: PASS

3. Teacher
   - Canonical route: /teacher
   - No legacy alias required
   - Primary nav target: /teacher
   - Status: PASS

4. Parent
   - Canonical route: /parent
   - No legacy alias required
   - Primary nav target: /parent
   - Status: PASS

5. Attendance
   - Canonical route: /attendance-dashboard
   - Allowed legacy/specialized routes: /attendance, /teacher/attendance
   - Primary nav target: /attendance-dashboard
   - Workspace route remains secondary
   - Status: PASS_WITH_DRIFT

6. Reporting / Summary
   - No standalone dashboard route in this pass
   - Capability preserved through role/admin/reporting flows
   - Do not create a standalone reporting nav item in this pass
   - Status: PASS

7. Scheduling / Rosters
   - Canonical route: /scheduling-dashboard
   - Allowed specialized routes: /classrooms, /aftercare/roster
   - Primary nav target: /scheduling-dashboard
   - Workspace/operational pages remain secondary
   - Status: PASS_WITH_DRIFT

8. Communications
   - Canonical route: /communications-dashboard
   - Allowed legacy/specialized route: /communications
   - Primary nav target: /communications-dashboard
   - Threads/workspace remain secondary
   - Status: PASS_WITH_DRIFT

9. Admissions
   - Canonical route: /admissions-dashboard
   - Allowed legacy/specialized routes: /admissions, /admissions/pipeline
   - Primary nav target: /admissions-dashboard
   - Pipeline/workspace remains secondary
   - Status: PASS_WITH_DRIFT

10. Gradebook
   - Canonical route: /gradebook-dashboard
   - Allowed legacy/specialized routes: /gradebook, /gradebook/:sectionId
   - Primary nav target: /gradebook-dashboard
   - Workspace/read-only paths remain secondary
   - Status: PASS

==================================================
D. DASHBOARD COMPLETION STANDARD
==================================================

A dashboard is only "done" when all of the following are true:

1. ROUTING
   - Canonical route exists
   - Any allowed alias works intentionally
   - No stale entry points point to wrong routes

2. NAVIGATION
   - Sidebar points to canonical route
   - Role entry points point to canonical route
   - Home dashboard shortcuts point to canonical route
   - Secondary workspace links are visually secondary, not primary

3. LAYOUT
   - Uses the shared dashboard shell
   - Uses consistent page header treatment
   - Uses consistent page spacing and section rhythm
   - Uses consistent card density

4. CONTENT
   - Has summary KPIs
   - Has recent activity / alerts / status area
   - Has at least one operational table/list
   - Has role-specific calls to action
   - Has useful empty states

5. PRODUCT FEEL
   - Looks like part of Crown
   - Reads like a working system
   - Uses realistic labels and school operations language
   - Does not look like a placeholder playground

==================================================
E. DASHBOARD FAMILY EXPECTATIONS
==================================================

1. ADMIN / HEAD OF SCHOOL
Must feel executive and operational:
- enrollment snapshot
- billing snapshot
- aid snapshot
- attendance flags
- communications alerts
- upcoming actions
- quick links to operational workspaces
- "school health" style summary

2. TEACHER
Must feel action-oriented:
- today's classes
- attendance shortcut
- gradebook shortcut
- student flags
- communication shortcut
- assignment/section status
- practical next actions

3. PARENT
Must feel family-centered:
- child cards
- balances
- assignments
- attendance summary
- messages/announcements
- calendar/events
- volunteer/service prompts where applicable

4. STUDENT
Must feel clear and useful:
- schedule
- assignments
- grades
- attendance
- service hours if present
- communications/reminders
- event and school-life visibility

5. BILLING
Must feel like finance ops:
- total outstanding
- aging or due-now signal
- recent payments
- invoices/obligations table
- exceptions/flags
- family account drilldown links

6. FINANCIAL AID
Must feel decision-oriented:
- applications in progress
- pending review
- awarded/not awarded summary
- budget utilization snapshot
- recommendation/exception queue
- family/application table

7. ATTENDANCE
Must feel operational:
- today absent/tardy counts
- flagged students
- class/grade filters
- attendance trends
- follow-up tasks
- link to teacher attendance workspace as secondary

8. COMMUNICATIONS
Must feel like command center:
- unread threads
- recent broadcasts
- pending responses
- communication categories
- message activity table
- threads workspace as secondary

9. ADMISSIONS
Must feel funnel-driven:
- inquiry count
- application count
- interview/follow-up queue
- stage pipeline summary
- admissions tasks
- pipeline workspace as secondary

10. GRADEBOOK
Must feel instructional and section-based:
- section summary
- grading status
- missing work / incomplete signals
- recent grade activity
- section links
- gradebook workspace secondary

11. SCHEDULING / ROSTERS
Must feel structural:
- schedule health
- section counts
- room/roster conflicts
- staffing or load summary
- quick links to operational roster pages as secondary

==================================================
F. WIDGET CONTRACT
==================================================

All widgets/cards/components used across dashboards must follow one visual and behavioral system.

1. Widget types allowed
- KPI stat card
- alert/status card
- recent activity list
- tabular operational list
- quick action card
- trend/summary block
- role shortcut group
- wizard progress/status card

2. Widget rules
- consistent padding
- consistent border radius
- consistent title treatment
- consistent value hierarchy
- consistent icon usage
- consistent empty state styling
- no random card styles per page
- no ad hoc spacing chaos

3. KPI cards
Each KPI card should include:
- label
- primary value
- optional delta/flag
- optional short helper text
- optional click target

4. Tables/lists
- strong headers
- readable row spacing
- consistent status pills
- action affordances that are obvious
- avoid overcrowding
- keep row actions predictable

5. Alerts/status widgets
- reserved for real operational attention items
- use consistent severity language
- avoid fake drama
- make alerts actionable

==================================================
G. WIZARD CONTRACT
==================================================

All wizards in Crown must feel like they belong to the same product, even if they support different modules.

Examples include:
- admissions onboarding
- enrollment/re-enrollment
- billing setup
- financial aid setup
- scheduling setup
- school profile/setup
- communications/broadcast setup
- any future guided configuration flow

Wizard rules:
1. Each wizard has a clear title and purpose
2. Step count must be visible
3. Progress indicator must be present
4. Back/Next buttons stay in consistent location
5. Save draft/save progress behavior must be clear if supported
6. Validation must be plain-language, not cryptic
7. Success state must be explicit
8. Step content width and spacing must be consistent
9. Field grouping must be logical and readable
10. No one-off wizard styling that breaks visual unity

Wizard step template:
- page title
- short explanatory subtitle
- grouped form sections
- optional side summary panel
- validation state
- primary/secondary action buttons
- persistent step navigation treatment

==================================================
H. STYLING / DESIGN SYSTEM CONTRACT
==================================================

The Crown frontend must look cohesive across dashboards, widgets, wizards, role pages, and workspaces.

1. General style direction
- modern but practical
- polished but not flashy
- operational, school-focused
- enterprise-clean with ministry warmth
- readable first, decorative second

2. Page structure
Every major page should generally follow:
- page title/header
- subheader/context
- KPI row or summary strip
- main operational content area
- secondary/supporting content area

3. Spacing
- use consistent outer page padding
- use consistent grid gaps
- use consistent card padding
- do not let different pages feel like they came from different products

4. Typography
- titles must be clearly hierarchical
- card headings consistent
- helper text subdued but readable
- avoid cluttered text blocks
- operational labels should be short and clear

5. Controls
- buttons consistent in size and priority
- filters/search bars styled consistently
- tabs and pills consistent across pages
- avoid random button variants that do the same thing

6. Color/status usage
- use status color consistently
- same meaning everywhere for success/warning/error/info
- avoid decorative color spam
- product should feel disciplined, not carnival-grade

7. Empty states
Every dashboard/workspace should have:
- short explanation
- next action suggestion
- optional quick action button
- Crown-consistent styling

==================================================
I. DASHBOARD / WORKSPACE RELATIONSHIP RULE
==================================================

Crown contains both dashboard surfaces and specialized workspace/operational pages.

Rule:
- dashboard = primary summary/control surface
- workspace = secondary drilldown/operational surface

Do not reverse this by accident.

Examples:
- Attendance dashboard is the summary/control surface
- Teacher attendance page is a specialized workspace

- Admissions dashboard is the summary/control surface
- Admissions pipeline page is specialized workspace

- Communications dashboard is the summary/control surface
- Threads list is specialized workspace

- Gradebook dashboard is the summary/control surface
- Gradebook RO / section route is specialized workspace

- Scheduling dashboard is the summary/control surface
- Classroom/roster pages are specialized workspace

==================================================
J. ROLE ENTRY / HOME ENTRY / LOGIN ENTRY RULES
==================================================

These must agree with the canonical contract.

1. Sidebar primary links -> canonical routes
2. HomeDashboard shortcut links -> canonical routes
3. LoginPage role routes -> canonical routes
4. RoleHomeRedirect -> canonical routes
5. Legacy/workspace routes can remain reachable, but should not be the primary destination unless intentionally designed that way

==================================================
K. KNOWN STATUS AFTER TONIGHT
==================================================

Local normalization contract:
- PASS for Billing
- PASS for Financial Aid
- PASS for Teacher
- PASS for Parent
- PASS for Reporting / Summary (as non-standalone by design)
- PASS for Gradebook

Local contract correct but with drift:
- Attendance
- Scheduling / Rosters
- Communications
- Admissions

Interpretation:
- local behavior is now aligned
- remaining issue is that some surfaces are still local-only or ahead of origin/main
- this is governance drift, not UI concept failure

==================================================
L. FILES MOST DIRECTLY INVOLVED IN NORMALIZATION
==================================================

Primary files touched/central to this work:
- frontend/dashboards/src/components/navigation/CrownSidebar.jsx
- frontend/dashboards/src/pages/HomeDashboard.jsx
- frontend/dashboards/src/pages/LoginPage.jsx
- frontend/dashboards/src/pages/RoleHomeRedirect.jsx
- frontend/dashboards/src/routes/router.jsx
- frontend/dashboards/src/config/dashboardRegistry.js
- frontend/dashboards/src/components/navigation/dashboardNavConfig.js

Use caution because repo contains other unrelated dirty changes outside this scope.

==================================================
M. NEXT SAFE WORK ORDER
==================================================

Do work in this order:

1. Preserve tonight's normalization truth
   - isolate normalization-related files
   - do not mix unrelated repo noise into the same change set

2. Reconcile the four PASS_WITH_DRIFT surfaces
   - Attendance
   - Scheduling / Rosters
   - Communications
   - Admissions

3. Tighten shared dashboard shell consistency
   - header patterns
   - KPI row patterns
   - table patterns
   - alert/empty state patterns

4. Tighten wizard consistency
   - step headers
   - progress treatment
   - actions
   - validation
   - spacing and layout

5. Tighten widget library consistency
   - stat cards
   - recent activity cards
   - alerts
   - tables
   - quick links
   - summary panels

6. Do a visual consistency pass
   - compare Admin, Teacher, Parent, Student, Billing, Financial Aid, Attendance, Communications, Admissions, Gradebook, Scheduling
   - remove anything that feels like a different product

==================================================
N. DO NOT DO THIS
==================================================

1. Do not create 5 new dashboards just because pages exist
2. Do not add route aliases casually
3. Do not let workspace pages become primary nav targets again
4. Do not treat Reporting/Summary as a random new standalone page in this pass
5. Do not widen scope into backend/data contracts unless needed
6. Do not commit normalization together with unrelated mess
7. Do not call placeholders "done"
8. Do not let each dashboard invent its own design language

==================================================
O. ACCEPTANCE CRITERIA FOR FRONTEND DASHBOARD MATURITY
==================================================

Frontend dashboard layer is considered mature for this phase when:

1. All approved canonical routes are stable
2. All primary nav targets align to canonical routes
3. Role/login/home entry points align to canonical routes
4. Workspace routes remain secondary and intentional
5. All dashboard pages use shared visual structure
6. Widgets/cards/tables feel standardized
7. Wizards feel like one product family
8. Empty states and alerts are consistent
9. The four drift surfaces are deliberately preserved/upstreamed
10. The product feels operational, not experimental

==================================================
P. SIMPLE FINAL TRUTH
==================================================

The dashboard problem is no longer "build more pages."
The dashboard problem is now:
- preserve clean routing truth
- reconcile drift
- standardize design
- standardize widgets
- standardize wizards
- polish the product experience

That is the lane.
Stay in it.
