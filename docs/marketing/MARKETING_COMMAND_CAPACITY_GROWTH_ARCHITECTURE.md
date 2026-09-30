# Crown Marketing Command and Capacity Growth Architecture

**Status:** Current product/engineering contract
**Purpose:** Define how Crown connects marketing, CRM, enrollment capacity, Portrait of the Graduate, financial aid, Admissions, and campaign economics without duplicating system authority.

## Canonical authorities

- **Admissions / Enrollment:** `applications.Application` and its event-backed admissions workflow remain the canonical prospect-to-enrollment authority.
- **Capacity:** `enrollment_period_wizard.GradeCapacity` is the source for grade-level target seats and whether new students are allowed.
- **Current enrollment:** `core.Enrollment` is the source for current enrolled students by academic year and grade.
- **Portrait outcomes:** `spiritual_life.PortraitDomain` is the source for school-defined Portrait of the Graduate outcomes.
- **Financial aid:** approved/accepted aid remains governed by the existing financial-aid/aid domains. CRM may consume summarized aid context but does not approve awards.
- **CRM / Marketing:** `crm_marketing` owns campaign targeting, attribution, touchpoints, follow-up state, and campaign economics. It does not replace Admissions.

## Capacity Growth Campaign

A capacity-growth campaign connects:

1. target academic year and grade;
2. verified target seats and current enrollment;
3. selected Portrait outcomes used as campaign value-proposition context;
4. target audience/segment criteria;
5. campaign budget and actual spend;
6. enrollment goal;
7. affordability strategy;
8. campaign-attributed leads;
9. touchpoints and follow-up cadence;
10. admissions conversion and enrollment outcome;
11. projected and actual campaign economics.

Empty seats are an internal planning signal. Family-facing messages should emphasize the school's educational and formation outcomes rather than vacancy or discounting.

## Attribution

CRM supports:

- first source;
- primary/influential source;
- conversion source;
- campaign identity;
- referral type and detail;
- touchpoint history.

Admissions submission must update an existing campaign-attributed CRM lead rather than create a duplicate unattributed lead.

## Follow-up playbooks

Stage-specific follow-up guidance is generated for inquiry, tour, application-started, application-submitted, and accepted stages. Playbooks guide staff action but do not silently send communications or change Admissions status.

## Financial-aid governance

Campaign affordability strategy may include a planned aid assumption for projection purposes.

Actual net-after-aid campaign economics must remain unavailable until aid is explicitly linked to campaign-attributed enrollments. Grade-level marketing/enrollment aid may be shown as context, but it must not be represented as campaign-attributed aid without verified linkage.

Portrait information may support messaging and family understanding of the school's mission. It must not be used as an opaque scoring mechanism for financial-aid awards.

## Economics

Campaign snapshots may calculate:

- projected gross tuition;
- projected aid;
- projected first-year net tuition after planned aid and campaign budget;
- projected lifetime net tuition based on configured retention years;
- actual gross tuition represented by campaign-attributed enrollments;
- actual spend;
- cost per enrollment.

Projected values must be labeled as projections. Actual net-after-aid remains unavailable until attribution is verified.

## External market and advertising data

Demographics, GIS/drive-time, church opportunity, preschool/feeder data, competitor intelligence, ad impressions, clicks, and external advertising spend are separate integrations.

Until verified sources are connected, Crown must report these areas as **not configured** rather than displaying estimated or sample values as live truth.

## Permissions

- `marketing.view`: read Marketing Command, campaign snapshots, and attribution.
- `marketing.edit`: create/manage campaigns and record campaign touchpoints.

All queries and writes are tenant scoped.

## Non-goals

This architecture does not create:

- a second admissions pipeline;
- a second financial-aid engine;
- a separate empty-seats module;
- a second Portrait of the Graduate store;
- an independent demographic truth source without verified external data.

