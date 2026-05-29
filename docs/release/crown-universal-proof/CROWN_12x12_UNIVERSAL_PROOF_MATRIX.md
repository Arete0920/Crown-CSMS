# CROWN 12x12 Universal Proof Matrix

> Authority Scope Notice (2026-05-29)
>
> This document is an evidence matrix artifact and not a controlling repository-level release authority source.
>
> Current controlling release-authority sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

Generated: 2026-04-28T00:21:44.6850018-04:00

This is the canonical proof matrix for all 12 major CROWN sections and all 144 subsections.

A subsection is not accepted as complete unless it has documentation, operational implementation evidence, and test/proof evidence. Product-taxonomy rows require canonical documentation and inventory classification evidence.

## Product Architecture / Taxonomy

Owner: TC / Product Owner

| # | Subsection | Definition | Required Proof |
|---:|---|---|---|
| 1 | Core Definition | Defines the mandatory platform and SIS backbone every school depends on. | Canonical docs must define Core and classify features that belong in Core. |
| 2 | Module Definition | Defines operating systems that depend on Core truth but are bounded units. | Docs and inventory must classify operational modules. |
| 3 | Add-on Definition | Defines optional products that integrate by contract or can stand alone. | Docs and inventory must classify add-ons and standalone candidates. |
| 4 | Tier Structure | Maps Core, Essentials, Complete, and Mission Suite to packaging. | Packaging docs must align tiers to architecture. |
| 5 | Standalone Product Strategy | Identifies tools that can operate outside the full Crown platform. | Standalone candidates must have boundaries and integration contracts. |
| 6 | Product Boundary Rules | Prevents good ideas from becoming uncontrolled dependencies. | Boundary rules must exist and be applied to inventory. |
| 7 | Roadmap Order | Defines build order: Core first, priority modules second, add-ons after stability. | Roadmap must explicitly enforce sequencing. |
| 8 | Market Positioning | Defines what Crown matches, beats, ignores, or defers against competitors. | Competitor/market docs must exist and inform product choices. |
| 9 | Customer Segments | Defines target schools and expansion boundaries. | Customer segment docs must exist and drive feature priority. |
| 10 | Feature Classification System | Tags every feature as Core, Module, Add-on, Keep, Rewrite, Drop, or Deferred. | Inventory must classify features and assets. |
| 11 | Pricing Logic | Connects architecture to commercial packaging and parent-funded revenue. | Pricing docs must match product layers. |
| 12 | Product Governance | Defines who approves scope, boundaries, tiers, and acceptance. | Governance docs must identify decision authority. |

## Platform Wiring / System Spine

Owner: Dev 1 / Core Platform Lead

| # | Subsection | Definition | Required Proof |
|---:|---|---|---|
| 1 | Authentication | Verifies user identity before access to school data. | Login APIs, auth middleware, and auth tests must exist and pass. |
| 2 | Role-Based Access Control | Controls what each user role can see and do. | Role matrix, enforcement code, and permission tests must exist. |
| 3 | Tenant / School Isolation | Ensures each school can only access its own data. | Tenant middleware, scoped querysets, and negative tests must pass. |
| 4 | Session Management | Maintains authenticated state and prevents stale or cross-school sessions. | Session refresh/logout paths and tests must exist. |
| 5 | Request Context | Carries user, school, role, and environment context through requests. | Backend request context and frontend context must be implemented. |
| 6 | Permission Matrix | Converts business rules into enforceable access controls. | Permission rules must be documented and tested by role. |
| 7 | Audit Trail Framework | Logs sensitive create, update, destroy, export, payment, and access actions. | Audit mixins/loggers and mutation tests must exist. |
| 8 | Notification Spine | Provides shared notification behavior for modules. | Shared notification services and delivery tests must exist. |
| 9 | Document / File Framework | Stores uploads, school docs, student docs, and evidence with access control. | Document models/storage and access tests must exist. |
| 10 | API Integration Layer | Provides controlled APIs for modules and external systems. | Versioned API, schema, and contract tests must pass. |
| 11 | Error Handling Standard | Logs failures cleanly and returns safe user-facing messages. | Error logging and safe response tests must exist. |
| 12 | Configuration Management | Controls secrets, flags, environment settings, and deploy values. | Environment config must be documented and secret-safe. |

## Backend / API Layer

Owner: Dev 1 + Dev 2

| # | Subsection | Definition | Required Proof |
|---:|---|---|---|
| 1 | Application Services | Contain business logic outside raw controllers. | Service-layer files and tests must exist. |
| 2 | API Endpoints | Expose backend functions through structured routes. | API route files and endpoint tests must exist. |
| 3 | Serializers / Schemas | Validate input and control output fields. | Serializers and serializer tests must exist. |
| 4 | Business Rules Engine | Enforces workflow and domain rules. | Business rule code and tests must exist. |
| 5 | Validation Layer | Rejects bad inputs before data is saved. | Validation code and negative tests must exist. |
| 6 | Workflow Services | Coordinates multi-step processes across modules. | Workflow services and end-to-end tests must exist. |
| 7 | Background Jobs | Runs async work such as emails, reports, reminders, and reconciliation. | Task files and task tests must exist. |
| 8 | Health Endpoints | Proves backend, database, cache, and deploy provenance are reachable. | Health endpoint must exist and runtime proof must pass. |
| 9 | Integrity Endpoints | Checks internal data/configuration consistency. | Integrity endpoint or equivalent proof script must exist. |
| 10 | Import / Export Services | Moves records in and out safely with validation and audit. | Import/export services and tests must exist. |
| 11 | Webhook Handlers | Processes external service events idempotently and securely. | Webhook handlers and signature/idempotency tests must exist. |
| 12 | Backend Test Harness | Runs unit, API, permission, tenant, and regression tests. | Backend tests must run green. |

## Database / Data Model

Owner: Dev 2 / SIS Data Lead

| # | Subsection | Definition | Required Proof |
|---:|---|---|---|
| 1 | Tenant Tables | Store schools and root tenant configuration. | Tenant models and migration tests must exist. |
| 2 | User Identity Tables | Store users, profiles, roles, and authentication metadata. | User identity models and permission tests must exist. |
| 3 | Student Master Record | Stores official student identity and school status. | Student model/API/tests must exist. |
| 4 | Household / Family Model | Connects students to guardians, billing, and communication relationships. | Household models and cross-tenant tests must exist. |
| 5 | Staff / Faculty Model | Stores staff, teachers, and school employee records. | Staff models and role tests must exist. |
| 6 | Enrollment Lifecycle Model | Tracks applicant, admitted, enrolled, withdrawn, alumni, and re-enrollment states. | Enrollment lifecycle rules and tests must exist. |
| 7 | Academic Structure Model | Stores school years, terms, grade levels, courses, sections, and rosters. | Academic structure models and tests must exist. |
| 8 | Attendance Data Model | Stores daily and period-level attendance. | Attendance model/API/tests must exist. |
| 9 | Grades / Report Card Model | Stores grade entries, calculations, grading periods, and report output. | Gradebook and report tests must exist. |
| 10 | Transcript / Credit Model | Stores official academic history, credits, GPA, and graduation progress. | Transcript/GPA tests must exist. |
| 11 | Financial Data Model | Stores charges, payments, balances, aid, and ledger records. | Finance models and ledger tests must exist. |
| 12 | Audit / Evidence Tables | Stores change records, access logs, approvals, and proof artifacts. | Audit/evidence models and tests must exist. |

## Frontend / User Interface

Owner: Dev 4 / Frontend UX Lead

| # | Subsection | Definition | Required Proof |
|---:|---|---|---|
| 1 | Application Shell | Provides shared layout, header, sidebar, and page frame. | Shared shell component and tests must exist. |
| 2 | Routing System | Maps URLs to screens with permission-aware routing. | Route config and route tests must exist. |
| 3 | Navigation Architecture | Controls menus, sidebars, breadcrumbs, and module entry points. | Navigation config and tests must exist. |
| 4 | Role-Based Layouts | Presents correct views for admins, teachers, parents, students, finance, and admissions. | Role dashboard tests must exist. |
| 5 | Dashboard Framework | Displays summaries, alerts, tasks, and metrics from real backend data. | Dashboard data tests and browser proof must exist. |
| 6 | Form System | Standardizes inputs, validation, save behavior, and error messages. | Form component and workflow tests must exist. |
| 7 | Table / List System | Standardizes grids, filtering, sorting, pagination, and exports. | Table/list tests must exist. |
| 8 | Wizard / Workflow UI | Guides multi-step processes without losing state. | Wizard UI tests must exist. |
| 9 | Design System | Defines colors, typography, spacing, cards, buttons, and visual consistency. | Theme/design system files and visual tests must exist. |
| 10 | Component Library | Provides reusable UI primitives for modules. | Component library and unit tests must exist. |
| 11 | Frontend State Management | Manages API data, loading, errors, selected school, filters, and auth state. | State hooks/context tests must exist. |
| 12 | Frontend Test Coverage | Proves pages, routes, forms, permissions, and flows work. | Frontend unit and E2E tests must run green. |

## SIS Core

Owner: Dev 2 / SIS Core Lead

| # | Subsection | Definition | Required Proof |
|---:|---|---|---|
| 1 | School Profile | Stores official school identity, logo, settings, and tenant configuration. | School profile model/API/UI/tests must exist. |
| 2 | Academic Year | Defines the operating school year for enrollment, reporting, attendance, and rollover. | Academic year model and rollover tests must exist. |
| 3 | Term / Grading Period | Breaks the year into reportable periods. | Term/grading-period tests must exist. |
| 4 | Grade Levels | Defines academic structure and placement. | Grade-level model/API/tests must exist. |
| 5 | Student Record | Stores official student identity and school status. | Student CRUD/API/tenant tests must exist. |
| 6 | Households / Guardians | Connects students to parents, guardians, family units, and communication preferences. | Household/guardian tests must exist. |
| 7 | Staff / Faculty Records | Stores teachers, administrators, and staff connected to roles and sections. | Staff/faculty tests must exist. |
| 8 | Enrollment Status | Controls active/inactive/admitted/withdrawn/alumni state. | Enrollment state-machine tests must exist. |
| 9 | Courses / Sections | Defines courses and class instances tied to teachers and students. | Course/section tests must exist. |
| 10 | Rosters | Assigns students and staff to classes, grade levels, homerooms, and groups. | Roster tests must exist. |
| 11 | Attendance | Records present, absent, tardy, and dismissal information. | Attendance API and workflow tests must exist. |
| 12 | Grades / Transcripts / Student Care | Stores academic outcomes, transcript history, discipline/care, and emergency essentials. | Academic/care record tests must exist. |

## Operational Modules

Owner: Dev 3 / Operations Module Lead

| # | Subsection | Definition | Required Proof |
|---:|---|---|---|
| 1 | Admissions | Manages inquiry through application, review, decision, and acceptance. | Admissions pipeline and E2E proof must pass. |
| 2 | Re-enrollment | Handles returning-family contracts, deposits, documents, and annual status updates. | Re-enrollment workflow tests must exist. |
| 3 | Billing / Tuition | Creates tuition plans, fees, schedules, charges, and household balances. | Billing model/API/ledger tests must pass. |
| 4 | Payments | Processes and reconciles payments through approved processors. | Payment processor and reconciliation tests must exist. |
| 5 | Communications | Manages announcements, messages, alerts, and school notifications. | Communications tests must exist. |
| 6 | Parent Portal | Gives parents access to student, billing, attendance, grades, messages, and tasks. | Parent portal Playwright proof must exist. |
| 7 | Teacher Portal | Gives teachers access to classes, attendance, grades, messages, and student context. | Teacher portal proof must exist. |
| 8 | Administrator Portal | Gives school leaders operational visibility and controls. | Admin dashboard proof must exist. |
| 9 | Scheduling | Manages periods, rooms, sections, teacher assignments, and schedules. | Scheduling tests must exist. |
| 10 | Activities / Athletics / Events | Manages clubs, teams, events, calendars, and participation. | Activities/events tests must exist. |
| 11 | Nurse / Health Office | Manages health visits, medication notes, alerts, and incident records. | Health office permission tests must exist. |
| 12 | Transportation / Food / Volunteer / Board Reporting | Covers buses, lunch, volunteer service, and leadership reports. | Second-wave module tests must exist. |

## Financial / Payment Infrastructure

Owner: Dev 3 + Finance

| # | Subsection | Definition | Required Proof |
|---:|---|---|---|
| 1 | Tuition Plan Engine | Defines tuition amounts, schedules, discounts, and payment options. | Tuition plan tests must exist. |
| 2 | Fee Management | Handles setup, registration, activity, lunch, and participation fees. | Fee tests must exist. |
| 3 | Charge Posting | Creates official receivables on family accounts. | Charge posting tests must exist. |
| 4 | Payment Collection | Accepts processor-supported payments. | Payment collection tests must exist. |
| 5 | Payment Reconciliation | Matches processor events to Crown balances and transactions. | Reconciliation tests must exist. |
| 6 | Balance Ledger | Maintains running household/family account balances. | Ledger immutability and reversal tests must pass. |
| 7 | Financial Aid Applications | Supports aid request intake and review. | Financial aid workflow tests must exist. |
| 8 | Scholarship / Aid Awards | Applies approved aid against tuition obligations. | Aid award tests must exist. |
| 9 | Family Participation Fee | Tracks recurring or required family-based fees. | Family fee tests must exist. |
| 10 | Refund / Credit Handling | Manages overpayments, credits, refunds, and adjustments. | Refund/credit tests must exist. |
| 11 | Finance Dashboard | Shows receivables, collections, aging, failures, and aid exposure. | Finance dashboard proof must exist. |
| 12 | Financial Audit Trail | Logs every financial mutation and sensitive finance action. | Financial audit tests must exist. |

## Faith / Mission / Differentiator Layer

Owner: Product + Dev 3

| # | Subsection | Definition | Required Proof |
|---:|---|---|---|
| 1 | Spiritual Life Tracking | Captures chapel, discipleship, and spiritual formation records. | Spiritual life model/API/UI tests must exist. |
| 2 | Service & Outreach | Manages service hours, outreach projects, and mission participation. | Service/outreach tests must exist. |
| 3 | Crown Compass | Provides school health assessment and improvement planning. | Compass tests or explicit deferred status must exist; complete gate requires operational proof. |
| 4 | Board Governance Suite | Supports board packets, meeting materials, and strategic dashboards. | Board governance tests must exist. |
| 5 | Christian PD Hub | Provides professional development resources for Christian educators. | PD Hub tests must exist. |
| 6 | Chaplain / Pastoral Care | Supports pastoral care workflows, referrals, and follow-up. | Pastoral care permission tests must exist. |
| 7 | Portrait of the Graduate | Tracks student growth against mission-defined outcomes. | Portrait tests must exist. |
| 8 | Mission Metrics | Aggregates indicators tied to faith, service, culture, and mission. | Mission metric tests must exist. |
| 9 | Discipleship Reflections | Allows guided reflection tied to formation goals. | Reflection tests must exist. |
| 10 | Accreditation / Improvement Planning | Organizes evidence, goals, and review cycles. | Accreditation tests/docs must exist. |
| 11 | Donor / Development Support | Tracks campaigns, donors, giving, and engagement. | Development tests must exist. |
| 12 | Mission Dashboard | Summarizes spiritual, service, school-health, and board indicators. | Mission dashboard proof must exist. |

## Integrations / External Services

Owner: Dev 5 / Integration QA

| # | Subsection | Definition | Required Proof |
|---:|---|---|---|
| 1 | Microsoft SSO / MSAL | Supports Microsoft identity login for schools. | MSAL code/config/tests must exist. |
| 2 | Google / Other SSO | Supports alternate identity providers when required. | Alternate SSO support or explicit deferred status must exist; complete gate requires proof. |
| 3 | CompuWerx Payment Integration | Connects parent subscription payment processing and reconciliation. | CompuWerx integration and test transaction proof must exist. |
| 4 | Stripe / Processor Abstraction | Keeps payment logic from hard-coding to one processor. | Stripe/processor tests must exist. |
| 5 | Twilio / SMS | Sends attendance and notification SMS. | SMS tests and safe config must exist. |
| 6 | Email Service Integration | Sends lifecycle emails and reminders. | Email integration tests must exist. |
| 7 | Sentry / Error Monitoring | Captures exceptions with PII-safe monitoring. | Sentry config and PII tests must exist. |
| 8 | Cloud Storage Integration | Stores documents, uploads, reports, and evidence. | Storage tests and permission checks must exist. |
| 9 | Calendar Integration | Syncs events, academic calendars, reminders, and school schedules. | Calendar tests must exist. |
| 10 | Import Connectors | Imports data from legacy systems and spreadsheets. | Import connector tests must exist. |
| 11 | Export / Reporting Connectors | Exports data to reporting, accounting, compliance, and board systems. | Export connector tests must exist. |
| 12 | Webhook / Event Bus | Publishes and receives events without invading Core. | Webhook/event tests must exist. |

## DevOps / CI/CD / Environments

Owner: Dev 5 / Release Lead

| # | Subsection | Definition | Required Proof |
|---:|---|---|---|
| 1 | Git Repository Structure | Defines repo layout for backend, frontend, docs, scripts, and infrastructure. | Repo structure must be clean and canonical. |
| 2 | Branch Strategy | Defines feature, repair, release, and main branch usage. | Branch policy docs and GitHub rules proof must exist. |
| 3 | Pull Request Workflow | Controls review, checks, approvals, and merge discipline. | PR workflow proof must exist. |
| 4 | GitHub Actions / CI | Runs lint, tests, builds, scans, and release gates. | Canonical workflow set must be present and not sprawling. |
| 5 | Deployment Pipeline | Moves code through dev, sandbox, staging, and production. | Deploy workflow and proof must exist. |
| 6 | Environment Strategy | Separates local, dev, sandbox, staging, and production. | Environment docs/config proof must exist. |
| 7 | Azure Hosting | Hosts API, frontend, database, storage, and secrets when ready. | Azure config/proof must exist. |
| 8 | Secrets Management | Stores credentials outside source code. | Secret scan must pass. |
| 9 | Database Migrations | Applies schema changes safely. | Migration check must pass. |
| 10 | Release Packets | Collects build, test, deploy, health, and known issue evidence. | Release packet proof must exist. |
| 11 | Rollback / Recovery | Defines how to restore stable code, data, and config. | Rollback docs/tests must exist. |
| 12 | Operational Monitoring | Tracks uptime, errors, latency, failed jobs, and health. | Monitoring workflow and alert proof must exist. |

## Governance / QA / Security / Evidence

Owner: Dev 5 + TC

| # | Subsection | Definition | Required Proof |
|---:|---|---|---|
| 1 | Definition of Done | Defines when a feature is truly complete. | DoD must exist and be enforced by tests. |
| 2 | Test Strategy | Defines unit, integration, API, frontend, browser, tenant, permission, and regression tests. | Test strategy and executable tests must exist. |
| 3 | Tenant-Isolation Testing | Proves one school cannot access another school's data. | Tenant-isolation test suite must pass. |
| 4 | Permission Testing | Verifies each role can only do allowed actions. | Role permission tests must pass. |
| 5 | Security Scanning | Checks code, dependencies, secrets, and configuration. | Security scans must be blocking and pass. |
| 6 | Compliance Documentation | Organizes FERPA, COPPA, privacy, retention, and DPA evidence. | Compliance docs must exist. |
| 7 | Audit Evidence Collection | Captures logs, screenshots, CSVs, health checks, and outputs. | Evidence output must be generated. |
| 8 | Scorecards / Readiness Gates | Converts proof into PASS/FAIL readiness. | Gate script and summary must exist. |
| 9 | Sandbox Proof Program | Verifies sandbox schools, credentials, demo data, dashboards, and feedback. | Sandbox proof tests must exist. |
| 10 | Issue / Risk Register | Tracks blockers, risks, owners, severity, mitigation, and review dates. | Risk register must be current. |
| 11 | Change Control | Controls high-impact changes to data, permissions, billing, auth, and deploys. | Change-control docs and branch rules must exist. |
| 12 | Go / No-Go Authority | Defines who can approve release, rollback, sandbox expansion, or production deploy. | Go/no-go authority and evidence gate must exist. |

