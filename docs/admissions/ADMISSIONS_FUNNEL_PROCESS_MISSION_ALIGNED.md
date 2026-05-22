# CROWN Mission-Aligned Admissions Funnel Process

## Visual Preview

- Quick visual design and runtime route map:
  - docs/admissions/ADMISSIONS_FUNNEL_VISUAL_PREVIEW.md

## Purpose
This document defines a quality, consistent admissions funnel for CROWN that:
- Starts with prospective families (not internal staff dashboards).
- Aligns to Christian school mission and values.
- Uses Portrait of the Graduate intent as formation guidance (not as an automated exclusion score).
- Reuses existing CROWN admissions APIs, routes, and role boundaries where possible.

## Existing Baseline (What You Already Have)

### 1. Admissions funnel data contract (strong)
Source: `docs/api/ADMISSIONS_API_CONTRACT.md`
- Canonical stages already defined:
  - `inquiry`
  - `tour_scheduled`
  - `tour_completed`
  - `application_started`
  - `application_submitted`
  - `in_review`
  - `accepted`
  - `waitlisted`
  - `declined`
  - `enrolled`
- KPI endpoint exists: `GET /api/v1/admissions/summary/`
- Drilldown endpoint exists: `GET /api/v1/admissions/drilldown/`
- Tenant + auth + RBAC expectations are documented.

### 2. Admissions backend logic (strong)
Source: `backend/applications/views_admissions.py`
- Deterministic stage computation exists.
- Conversion and velocity metrics are computed.
- Stage filtering and source filtering exist.
- Access controlled with `IsAuthenticated` and `admissions.view`.

### 3. Admissions UI and route wiring (partial)
Sources:
- `frontend/dashboards/src/routes/router.jsx`
- `frontend/dashboards/src/routes/paths.js`
- `frontend/dashboards/src/config/dashboardTemplates/admissionsDashboard.js`
- Current admissions route (`/admissions`) serves internal admissions dashboard experience.
- Pipeline route exists (`/admissions/pipeline`).
- Wizard route exists (`/onboarding`) but is role-guarded for internal roles.

### 4. Mission/portrait infrastructure (partial)
Sources:
- `backend/spiritual_life/services.py`
- `backend/portrait/services.py`
- `docs/canon/CROWN_DISCERNMENT_PRINCIPLES.md`
- Mission metrics service exists and aggregates spiritual-life + portrait signals.
- Portrait service currently returns safe-zero stub values (no live portrait domain models yet).
- Canon principles already require human judgment, explainability, and auditability for high-impact decisions.

## Key Gap Summary
- You have an internal admissions operations funnel.
- You do not yet have a dedicated, public, prospective-family-first application entry process.
- Mission alignment logic is conceptually present, but portrait evidence is not yet operationalized in live admissions decision support.

## Quality Admissions Funnel (Target Process)

### Stage 0: Interest (Public)
Objective:
- Capture family interest with clear mission/values presentation and low-friction next step.

Entry:
- Public website CTA: `Start Your Application` and `Request Information`.

Required outputs:
- Lead record with source attribution.
- Family consent and communications preference.

Exit criteria:
- Lead created and acknowledged (email/SMS confirmation).

Owner:
- Marketing + Admissions Coordinator.

### Stage 1: Inquiry
Objective:
- Gather initial family/student context and mission-fit conversation points.

Required artifacts:
- Inquiry form (student grade target, family goals, faith/church context optional, prior school context).
- SLA timer for first response.

Exit criteria:
- Family receives next-step plan and tour/interview options.

Owner:
- Admissions Coordinator.

### Stage 2: Discovery / Tour
Objective:
- Mutual discernment: family evaluates school mission; school understands student/family needs.

Required artifacts:
- Tour attendance record.
- Discovery notes with structured tags (academic readiness, support needs, mission alignment conversation).

Exit criteria:
- Tour completed and family invited to application.

Owner:
- Admissions Team + Campus Host.

### Stage 3: Application Start
Objective:
- Family starts formal application with save/resume.

Required artifacts:
- Applicant account.
- Checklist initialized (forms, docs, references, assessments, fees if applicable).

Exit criteria:
- Application status transitions to `application_started`.

Owner:
- Family self-service + Admissions Support.

### Stage 4: Application Submitted
Objective:
- Ensure package completeness and integrity.

Required artifacts:
- Submission timestamp.
- Document completeness validation.
- Fraud/duplicate flags.

Exit criteria:
- Application status transitions to `application_submitted` and enters review queue.

Owner:
- Admissions Operations.

### Stage 5: Holistic Review (Human-Led)
Objective:
- Evaluate academic readiness, support fit, and mission alignment without reducing persons to scores.

Required artifacts:
- Reviewer rubric with auditable notes.
- Mission/values reflection section.
- Optional portrait-oriented indicators (service, character, growth mindset) used as supportive evidence.

Guardrails (from canon principles):
- No automated final decision.
- Human review required for acceptance/waitlist/decline.
- Explainability notes mandatory.

Exit criteria:
- Recommendation prepared for decision authority.

Owner:
- Admissions Director + Review Committee.

### Stage 6: Decision
Objective:
- Deliver clear, compassionate, and auditable outcomes.

Outcomes:
- Accepted
- Waitlisted
- Declined

Required artifacts:
- Decision rationale (internal).
- Family communication template and timeline.

Exit criteria:
- Decision event recorded and communicated.

Owner:
- Admissions Director.

### Stage 7: Enrollment Conversion
Objective:
- Convert accepted families to enrolled students with minimal friction.

Required artifacts:
- Enrollment packet completion.
- Deposit/payment confirmation.
- Enrollment intent confirmation.

Exit criteria:
- Stage transitions to `enrolled`.

Owner:
- Enrollment Coordinator + Finance.

### Stage 8: New Family Onboarding
Objective:
- Transition from admissions to student success and family integration.

Required artifacts:
- Student/family profile activation.
- Orientation tasks and communications.
- Initial pastoral/community welcome touchpoint.

Exit criteria:
- Onboarding checklist complete and handoff to school operations.

Owner:
- Registrar + Student Life + Family Engagement.

## Mission and Portrait Integration Model

### Christian mission alignment (required)
Use mission alignment as a relational and formative conversation, not a mechanical filter.

Artifacts to capture in review:
- Family understanding of school mission.
- Commitment to partnership with school values and community norms.
- Student growth potential in faith, character, service, and scholarship.

### Portrait of the Graduate alignment (recommended rubric)
Track evidence for these domains (editable per school):
- Faith and spiritual formation
- Character and integrity
- Service and community engagement
- Academic stewardship
- Leadership and collaboration
- Resilience and growth

Important:
- Portrait indicators guide support planning and formation pathways.
- They do not function as an opaque auto-score for denial.

## Funnel KPIs and Quality Controls

### Core KPI set (must-have)
- Inquiry volume by source
- Inquiry -> Tour conversion
- Tour -> Application start conversion
- Start -> Submission conversion
- Submission -> Decision conversion
- Acceptance -> Enrollment conversion
- Time in stage (velocity)
- 7-day no-follow-up lead count
- Incomplete application aging (72h, 7d, 14d)

### Mission-quality KPI set (should-have)
- Mission conversation completion rate
- Family partnership commitment completion rate
- Post-enrollment mission-fit confidence pulse (30/90 day)
- Early attrition by source/cohort (first 90 days)

### Operational SLAs (recommended defaults)
- New inquiry first response: <= 1 business day
- Post-tour follow-up: <= 2 business days
- Submitted application completeness check: <= 2 business days
- Decision communication after committee review: <= 5 business days

## Role and Permission Model (Admissions Funnel)

Public/Family:
- Can create inquiry
- Can start and submit application
- Can upload documents and track status

Admissions Staff:
- Can triage inquiry, update pipeline stages, review applications

Admissions Director:
- Can finalize decision
- Can override with rationale

Registrar/Finance:
- Can execute enrollment conversion tasks

Audit/Leadership:
- Read-only access to KPI, SLA, and fairness/audit views

## Implementation Sequence (Using Current CROWN Assets)

### Phase 1: Stabilize and expose family-first entry
- Add dedicated public route for inquiry/application start (do not land on internal `/admissions`).
- Keep `/admissions` and `/admissions/pipeline` internal staff surfaces.
- Map public entry to existing canonical stage flow and events.

### Phase 2: Make application wizard family-usable
- Re-scope wizard access for family applicant context.
- Preserve internal admin setup wizards separately.
- Add save/resume and checklist completion states.

### Phase 3: Add mission/portrait review artifacts
- Add structured mission conversation fields to review.
- Add portrait evidence collection fields and reviewer notes.
- Keep decision human-led with required rationale logging.

### Phase 4: Quality and consistency hardening
- Add SLA monitoring and backlog alerts.
- Add drop-off analytics by stage and source.
- Add 30/90 day post-enrollment mission-fit pulse for feedback loop.

## Definition of Done (Admissions Funnel)
The funnel is considered production-quality when:
- Prospective families start in a public/family intake flow, not internal ops dashboards.
- Every application has auditable stage transitions and owner accountability.
- Decisioning is human-reviewed and explainable.
- Mission and portrait evidence is captured consistently.
- Enrollment conversion and onboarding handoff are tracked to completion.
- KPI and SLA dashboards are live and trusted by leadership.

## Immediate Next Step Recommendation
Use this process as the canonical admissions operating model, then implement Phase 1 and Phase 2 first so external family UX matches the intended Christian mission-driven journey.
