# CROWN Dependency-Based Completion Plan

**Document ID:** CROWN-GOV-005  
**Status:** ACTIVE — Initial Controlled Baseline  
**Parent authority:** `docs/governance/CROWN_BUYER_READY_COMPLETION_CANON.md`  
**Repository evidence SHA:** `7fb6ca623e541d3f59a482e5bb13769b998403e8`  
**Plan date:** 2026-07-24  
**Owner:** John Megahan  
**Controlling execution issue:** #1587

## Governing rules

1. No new feature scope enters this program without controlled scope approval.
2. A later stage may not pass while a prerequisite stage remains materially incomplete.
3. Repository implementation, test evidence, deployed-runtime proof, external-platform evidence and independent review remain separate.
4. Any material source, configuration or infrastructure change invalidates affected downstream evidence.
5. Documentation work cannot close an executable, operational, security, legal, financial or transfer requirement without its required evidence.
6. External payment processing remains excluded and fail closed until separately authorized.
7. Buyer-specific transfer execution remains excluded until a buyer is selected; universal transfer readiness remains in scope.

## Stage 0 — Authority and hygiene control

### Purpose

Create one authoritative governance framework and remove obsolete information from active decision paths.

### Work

- maintain the buyer-ready completion canon;
- establish requirement, assessment, risk and completion-plan controls;
- merge or disposition safe archive PR #1586;
- build the superseded-information register;
- reconcile subordinate product, release and operations authorities;
- correct stale links without destroying historical evidence.

### Exit criteria

- controlled hierarchy is active;
- no competing active completion authority remains;
- every historical authority is retained, watermarked or registered;
- every open program lane references stable canon requirement IDs.

## Stage 1 — Complete source and surface census

### Dependencies

Stage 0.

### Work packages

1. **Backend census**
   - installed apps and app configs;
   - models and migrations;
   - services, selectors, repositories and managers;
   - serializers, schemas, APIs and URL patterns;
   - middleware, signals, commands, jobs, schedulers and background tasks;
   - imports, exports, file uploads and reports;
   - integrations, webhooks and disabled surfaces.
2. **Frontend census**
   - applications and build entry points;
   - routes, redirects, aliases and guards;
   - pages, forms, tables, reports and exports;
   - dashboards, widgets, drilldowns and navigation;
   - persona surfaces and responsive variants.
3. **Wizard census**
   - all 28 registry entries;
   - app, URL, model/session, steps, validation, commit and rollback behavior;
   - permissions, tenant binding, tests and runtime path.
4. **Platform and repository census**
   - workflows, triggers, checks, artifacts and branch-protection roles;
   - infrastructure definitions and environment variables;
   - third-party dependencies and licenses;
   - evidence packages and operating documents.

### Required output

One authoritative application-surface inventory. Each item must be classified as `ACTIVE`, `DISABLED_FAIL_CLOSED`, `EXCLUDED_PAYMENT_PROCESSING`, `EXCLUDED_HANDOFF`, `NOT APPLICABLE`, `SUPERSEDED`, or `REMOVED`, and mapped to exactly one proof mechanism.

### Exit criteria

- no installed app, route, dashboard, wizard, API, job, integration or workflow remains unmapped;
- canonical paths and compatibility aliases are distinguished;
- owner, persona, tenant scope, sensitivity and evidence mechanism are recorded.

## Stage 2 — Core control and canonical-data convergence

### Dependencies

Stage 1 inventory for affected surfaces.

### Ordered work

1. tenant/school context and privileged override;
2. identity, authentication, session and user lifecycle;
3. role/action permission and entitlement mapping;
4. audit events and sensitive-access logging;
5. school, academic year, term and grade-level truth;
6. family, guardian and household authority;
7. student master authority;
8. enrollment/registrar authority;
9. academics courses, sections, rosters and relational integrity;
10. retention, rollover, correction, deletion and compatibility controls.

### Required proof

- authoritative model and write path;
- migration and rollback behavior;
- normal, queryset, bulk, import, task, admin and raw-SQL boundaries;
- tenant and role negative tests;
- reconciliation queries;
- cross-module consumer map;
- compatibility retirement criteria.

### Exit criteria

- no unresolved Critical duplicate-truth or tenant-integrity gap;
- Core records have one authoritative owner and approved service paths;
- active compatibility behavior is bounded, tested and documented.

## Stage 3 — Dependency-ordered functional verification

### Dependencies

Stage 2 for each dependent domain.

### Batch A — Core daily operation

- school/year/grade;
- staff/user/role;
- family/guardian/household;
- student;
- enrollment/registrar;
- courses/sections/rosters;
- attendance;
- gradebook;
- transcript/report card/graduation;
- student care/discipline.

### Batch B — Commercial school operation

- admissions;
- re-enrollment;
- provider-neutral billing, tuition, accounting and ledger;
- financial aid;
- communications;
- parent, teacher and administrator portals.

### Batch C — Operational expansion

- scheduling;
- activities and athletics;
- health office;
- transportation;
- food service;
- facilities;
- safety/security;
- HR;
- IT support.

### Batch D — Mission, enrichment and advancement

- fine arts;
- library/media;
- extended care;
- summer camp;
- spiritual life/chaplaincy;
- service/outreach/portrait;
- volunteer management;
- advancement;
- alumni;
- board governance;
- curriculum/PD;
- network analytics.

### Batch E — Platform operations

- implementation success;
- data migration;
- integrations/automation;
- compliance audit;
- revenue operations;
- release reliability;
- dashboard certification center.

### Per-module exit criteria

- domain ownership complete;
- model, service and API verified;
- frontend primary and negative paths verified;
- tenant, permission, entitlement and audit evidence current;
- import/export/report behavior verified where applicable;
- cross-module side effects reconciled;
- known limitations recorded;
- runtime evidence path assigned;
- independent review requirement identified.

## Stage 4 — Dashboard, wizard and persona reconciliation

### Dependencies

Source modules verified sufficiently to feed their surfaces.

### Dashboards

For every dashboard:

- source module and summary service;
- schema and provenance;
- freshness and stale/unavailable behavior;
- sensitivity, redaction and small-cell suppression;
- tenant and dashboard-key authorization;
- metrics, alerts, work queue and activity;
- drilldown reconciliation;
- export policy;
- browser/runtime evidence;
- independent review.

### Wizards

For every registered wizard:

- prerequisites and persona;
- step contract and validation;
- draft/session persistence;
- idempotency and duplicate submission;
- transaction and rollback boundary;
- audit and permission behavior;
- resulting records and cross-module effects;
- negative and interruption paths;
- runtime evidence.

### Personas

Verify school administrator, teacher, parent, student, board and each specialist role through direct-route and navigation-driven workflows.

### Exit criteria

- every dashboard and wizard is `PASS`, `PARTIAL`, `FAIL`, `NOT APPLICABLE`, `SUPERSEDED` or `REMOVED` with evidence;
- no production-visible sample or fallback is undisclosed;
- no persona surface depends on navigation hiding for security.

## Stage 5 — Exact-SHA production certification

### Dependencies

Stages 1-4 for the authorized release scope.

### Work

- settle and freeze one candidate SHA;
- verify all required checks terminal and green;
- build and record immutable frontend/backend artifacts;
- capture configuration and infrastructure identities;
- deploy the unchanged candidate;
- run mapped backend, API-contract, crawler and Playwright campaigns;
- record authentication, tenant, route, network, console, screenshot, accessibility and provenance evidence;
- fail on omitted active surfaces or identity mismatch;
- restart certification if source, configuration or infrastructure changes.

### Exit criteria

One complete production-certification package tied to one unchanged release tuple.

## Stage 6 — Operational, infrastructure and security proof

### Dependencies

Stable candidate and current operating environment.

### Work

- application rollback drill;
- database restore and reconciliation drill;
- measured RTO/RPO acceptance;
- external secret-store access, audit, rotation, failed rotation, revocation and break-glass exercises;
- monitoring, alert and incident-response exercise;
- backup, retention and recovery evidence;
- environment, service account, domain, certificate, vendor and subscription inventory;
- software supply-chain, SBOM, license and vulnerability review;
- file-upload and sensitive-data controls.

### Exit criteria

All Critical operational and security controls `PASS` or formally accepted through a valid exception process where the canon permits it.

## Stage 7 — Compliance, diligence and transfer readiness

### Dependencies

Accurate technical and operational baseline.

### Work

- student-data inventory and flow maps;
- FERPA, COPPA, PPRA, CIPA and applicable state-law claim analysis;
- privacy notices, DPA, terms, retention and incident documentation;
- qualified legal and security review;
- IP chain of title and evidence-backed contributor ledger;
- open-source and commercial license inventory;
- commercial, pricing, pipeline, adoption, revenue, cost and projection claims register;
- corporate, tax, insurance, contract and vendor package indexes;
- repository, cloud, domains, secrets, subscriptions and account transfer inventory;
- architecture, runbook and knowledge-transfer package;
- founder-unavailable continuity rehearsal.

### Exit criteria

- universal buyer diligence package current;
- all material claims supported or clearly qualified;
- known limitations and risks disclosed;
- a qualified operator can understand and operate CROWN without undocumented founder-only knowledge;
- buyer-specific execution remains unclaimed until authorized.

## Stage 8 — Final reconciliation and decision

### Dependencies

All prerequisite stages.

### Work

- update current-state assessment, requirement matrix, risk and limitation registers;
- reconcile release notes, changelog, architecture and operations authorities;
- verify no unresolved Critical requirement or undisclosed High risk;
- record required independent reviews;
- conduct final same-identity ceremony;
- record Founder/Product Owner decision;
- when applicable, apply buyer-specific overlay and transfer acceptance.

### Exit criteria

An explicit evidence-backed decision for each state: Implemented, Verified, Release Certified, Production Authorized, Buyer Ready and Transfer Complete. States may not be combined or inferred.

## Immediate executable queue

1. Complete Stage 0 controlled artifacts and merge bounded authority-hygiene work.
2. Generate Stage 1 repository census from the immutable evidence SHA.
3. Convert the five product planning matrices into current evidence matrices beginning with the first ten dependency-ordered modules.
4. Reconcile routes, dashboards and all 28 wizards to the census.
5. Close Critical Core-data, tenant and RBAC evidence gaps before attempting final runtime certification.
6. Preserve full-production target and payment fail-closed boundary throughout execution.
