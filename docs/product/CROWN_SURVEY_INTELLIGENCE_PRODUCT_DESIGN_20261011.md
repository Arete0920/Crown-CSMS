# CROWN Survey Intelligence — Product Design v0.1

**Status:** PROPOSED — product design and engineering backlog, not production authority  
**Date:** 2026-10-11  
**Tracking:** [Issue #204](https://github.com/Arete0920/Crown-CSMS/issues/204)  
**Provenance:** Current `main` resolved as `ee01a48bfa3bc0502de3d5a1ee03e2b1be9f3806` when scoped. Historical unmerged recovery snapshot: PR #39, `99eff0f0dec80b2565bfe76ac13e23d84583a350`.  
**Supersession:** None. Consistent with the current Architecture Canon, Compass Canon, privacy specification, module completion matrix, and release status. This is a controlled supporting proposal.

## Product outcome

One Survey Intelligence domain owns instrument versions, invitations, responses, permitted analysis and audit evidence. Kingdom Path and Crown Compass are **consumers**, not alternate databases. The product succeeds when leaders can move from responsibly collected evidence, to transparent interpretation, to a documented and measurable improvement action. It must never infer faith or personal character scores for individual students.

### Architectural boundary

```text
               CROWN Core (authoritative identity, school, permissions)
                                  |
               Survey Intelligence domain (module data owner)
       [instruments] [consent] [distribution] [responses] [audit]
                                  |
           privacy + reporting contract / cohort-scoped aggregates
                       /                         \
           Kingdom Path                      Crown Compass
    admissions/affordability             climate/leadership/mission
       /growth strategy                    governance/board insight
                       \                         /
                   Evidence-to-Action initiatives
                     (school-owned, human-reviewed)

Solomon explains approved aggregate results and implementation playbooks only.
Discernment remains inside Compass; no forecast until validated and approved.
```

Cross-domain consumption must use approved scoped services/API contracts, not imports that bypass domain policy. No individual response records are sent to external models.

## Information architecture

Main navigation: **School Insights > Survey Intelligence**, with tabs:

1. **Overview** — current collections, due dates, participation reporting (only when permissible), validated findings, action follow-up.
2. **Survey Library** — seven recovered enrollment instruments plus, later, age-appropriate climate/leadership libraries; drafts and published versions distinguished.
3. **Create & Deliver** — choose purpose/audience, preview accessible questionnaire, define anonymous vs confidential vs identified collection, notice/consent, window, delivery, reminders, publish.
4. **Results & Insights** — safe response counts, distributions, domains, group comparability, suppression explanations, years and cohorts, data provenance, confidence/research limitations.
5. **Improvement Plans** — review finding, authorize response, owner, due date, baseline, follow-up, documented action, outcome review.
6. **Settings & Governance** — permissions, privacy policy, public invitation limits, survey lifecycle, retention, export audit, approved instrument versions.

**Additional entrypoints:** Kingdom Path > Family & Market Research; Crown Compass > Institutional Climate / Leadership & Mission. These are permission-scoped views of the same service and must never expose more than the underlying access contract.

## First four product screen specifications

### Screen A — Overview
- Header: Survey Intelligence | School: [current tenant] | Academic year: [actual year] | [Create survey] (permission-controlled).
- KPI row: Active surveys; completed responses and response rate **where an eligible invitation denominator exists**; surveys closing soon; open improvement actions. Avoid false `0%` response rate when denominator is absent.
- Survey list: Name | Audience | Data mode | Version | Window/status | Authorized participation indicator | owner action. Unavailable is shown as such.
- Finding panel: each signal links to a provenance-bearing, suppressed-safe report. If no eligible evidence: “No reportable results yet.”
- Action list: title, owner, follow-up date, source finding, status.
- All sample values for design/mockups must be prominently marked **ILLUSTRATIVE** and never committed as live API responses.

### Screen B — Survey Builder
A guided sequence: **Purpose > Audience > Privacy/Notice > Questions > Distribution > Review & Publish**.
- Purpose: Inquiry / Post-tour / New Family / Parent pulse / Re-enrollment / Lost prospect / Exit / Custom; later Climate / Employee / Leadership.
- Mandatory data mode: Anonymous; Confidential/limited access; Identifiable & disclosed. Explicit explanation of what each does and does not guarantee.
- Question editor: version-controlled, required/optional, Likert/choice/multiselect/text/yes-no; scales anchored consistently. Branching logic later.
- Public preview must match respondent view and use mobile-first accessible controls.
- Publish freezes instrument version and its consent/legal notice; subsequent changes create a new version. Close/revoke/expire audited.
- Do not ship the historical seven templates unreviewed as scientifically validated instruments.

### Screen C — Results & Insights
- Show question/sample provenance, count of eligible invitations and responses when measurable, date window, missing/partial responses, and whether respondent identity is anonymous.
- Charts: distribution first, mean where meaningful; trend only among comparable question versions and cohorts.
- Subgroup results require configured and tested minimum sample thresholds and complementary suppression (no back-calculation).
- Qualitative comments: restricted handling, PII review, no public raw comments by default.
- Differentiation: switch between **Kingdom Path interpretation** (market/funnel/tuition context) and **Compass interpretation** (institutional climate/mission/leadership) but enforce downstream policy and data minimization.
- Do not show retention “risk score” without validated model and review.

### Screen D — Evidence-to-Action
- Source finding: stable report and data window; finding text; stated limitations.
- Initiative: approved objective, action steps, accountable owner, milestone dates, projected and observed outcome (clearly separated), evidence link.
- Review loop: reevaluate with a comparable future survey + operational KPIs; record human decision, not autonomous school action.
- Distinguish survey sentiment from verified enrollment/financial outcome data.

## Survey inventory

**Recovered historical instrument categories (32 starter questions; not currently wired in main):**
Inquiry (4), Post-tour (4), New family (5), Parent pulse (7), Re-enrollment intent (3), Lost prospect (4), Exit (5). `custom` is supported by the historical model without starter questions.

**Proposed, separately tested future libraries:** Student climate (age appropriate), employee climate, graduate/alumni, head-of-school/board governance, instructional experience. No third-party proprietary questions copied.

## Contract and domain model (target, not asserted implemented)

- SurveyDefinition: tenant, purpose, creator/owner, target audience, program classification, notice/access policy.
- SurveyVersion: immutable published question set, scales, timing, consent requirements, hash and approval trace.
- SurveyQuestionVersion: prompt, stable analytical key, constraints, skip logic when introduced, order and domain tags.
- SurveyInvitation: distribution channel, optional recipient only for explicitly identified/managed collection; response-rate denominator and invitation lifecycle without linking anonymous response answers to the recipient.
- SurveyResponse: immutable submission, survey version, school ID, data mode, collection cohort/window, provenance and cryptographically random id; identity reference only when permitted.
- SurveyAnswer: typed, validated answer belonging to the same survey version and tenant.
- AggregateReport: approved filters, provenance/query version, threshold/suppression markers and timestamp; no insecure cache spill across tenants.
- ImprovementInitiative: school-scoped linked aggregate finding, accountable owner, human-approved actions, dates, follow-up status and audit.
- ExportAudit/AccessAudit: who requested sensitive access/export, when, why, which filters and school.
- Separation: never share response identities or raw comments with downstream add-ons unless separately permitted and justified; no model can bypass source permissions.

### Privacy requirements

- Anonymous means neither APIs, exports, raw logs nor ordinary administration tables retain a recoverable respondent link; collecting invite completion metadata must not enable trivially rejoining identity to answer contents.
- Confidential does **not** mean anonymous. Restrict raw responses and disclose actual access to respondents.
- Identified mode must show the intended school use and limit fields by role/purpose.
- Handle FERPA/COPPA/PPRA and state applicability through school-configured notice/inspection/consent/opt-out workflows with legal review; no blanket school applicability assumption.
- Enforce tenant scope in joins, foreign keys, caches, object-ID reads, aggregated filters, exports and all write paths.
- Define deletion/archive/legal-hold schedules and authorized subject-access workflows.
- Design small-cell and complementary suppression before shipping segmentation/drilldown.
- Separate surveys of minors or protected subjects from marketing and unrelated analytics.
- Independent technical security testing is a required acceptance step.

## Prioritized deliverables and readiness gates

| ID | Priority | Scope | Blocking completion evidence |
|---|---|---|---|
| SI-01 | P0 | Recovery compatibility audit / domain authority | Current main & historic snapshots mapped; no destructive migration |
| SI-02 | P0 | Collection modes, privacy & governance contract | Threat model, access/notice/retention/export matrix reviewed |
| SI-03 | P0 | Versioned domain models & migrations | Schema/test validation, reversible migration rehearsal |
| SI-04 | P0 | Secure public/authenticated submission | Tenant, authorization, expiry, tampering, validation, replay, transaction negative tests |
| SI-05 | P0 | Real survey API/E2E test suite | End-to-end school/recipient and cross-tenant proof |
| SI-06 | P0 | Statistical/report privacy contract | Correct cohort counts, denominator, version, suppression and provenance tests |
| SI-07 | P1 | Survey library/editor/publishing UX | Screen reader/mobile flow and permission checks |
| SI-08 | P1 | Invitation/reminder & lifecycle UX | Verified sending/status, opt-out and zero-PII leaks |
| SI-09 | P1 | Kingdom Path market-study recovery | Source provenance and governed CRM/admissions/aid interfaces |
| SI-10 | P1 | Kingdom Path survey analyses | Verified context, human-readable report, non-sample proof |
| SI-11 | P1 | Pilot school workflow | Admin creation -> respondent submit -> safe report -> export/revoke end-to-end |
| SI-12 | P2 | Climate instruments | Age/stakeholder pretesting, governance review |
| SI-13 | P2 | Leadership / trustee instrument suite | Conflict and access matrices, confidential review |
| SI-14 | P2 | Compass aggregate integration | Board-role negative access, reporting and provenance proof |
| SI-15 | P2 | Evidence-to-Action initiatives | Human-approval and follow-up lifecycle API/UI tests |
| SI-16 | P3 | Longitudinal/reliability methodology | Peer methodological review and comparability rules |
| SI-17 | P3 | Opt-in benchmarks / Discernment | Opt-in policies, viable cohorts, model validation & independent safety review |

P0/P1: focus on bounded school administration and Kingdom Path pilot; no pressure to block Jan 2027 Core go-live if an add-on is not ready. P2/P3: after pilot evidence and release sequencing review. Scheduling is subject to current launch-critical reliability work.

## Bounded PR train (implementation, not this design PR)

1. Source recovery compatibility inventory + schema/privacy ADR.
2. Restore versioned survey domain models, migrations and narrow unit coverage.
3. Secure survey API + request/tenant/negative tests.
4. Production-safe reporting service, suppression and provenance tests.
5. Admin create/preview/publish UX and respondent page E2E.
6. Kingdom Path market-study recovery and governed consumer interface.
7. Compass climate/leadership instrument pilots, then Evidence-to-Action.

**Policy:** Keep PRs under repository hygiene limits, preserve CI/security gates, independently verify exact heads, never merge historical oversized PR #39, and never claim deployment from repository source alone.

## Acceptance language

Until exact-head code, functional journeys, UI, reporting, privacy and release evidence exist, report **“Designed / not yet implemented”**. Do not mark any stage Certified based solely on a plan, route, registry row, superficial smoke test, sample chart or merged doc.

## Research / third-party independence

External vendor products are market-learning references only, with no partnership assumption. Use independently authored questions, original presentation and code, established public research methods where legitimately usable, and legally cleared sources. Do not copy competitors' proprietary survey instruments, question wording, reports, designs, algorithms, implementation logic, code or datasets. Record the independent origin, version, reviewer and permissions for each proposed survey instrument; conduct pre-publication intellectual-property and licensing review.
