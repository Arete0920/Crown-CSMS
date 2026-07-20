# CROWN Modules and Dashboards Verification Packet

**Status:** Active planning-control packet  
**Parent canon:** `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`  
**Release authority:** `docs/CURRENT_RELEASE_STATUS.md`  
**Originally created:** 2026-06-09  
**Authority alignment updated:** 2026-07-20

## Purpose

This packet defines the evidence and review path for CROWN module and dashboard planning. It does not approve the canon, certify a module or dashboard, authorize sandbox or production use, or change release posture.

## Authority model

TC Megahan is the Founder/Product Owner and accountable decision owner. Repository checks, tests, static analysis, browser evidence, AI-assisted analysis, and other automation may produce findings and supporting evidence. They do not provide human authorship, independent review, approval, acceptance authority, certification authority, or release authority.

A qualified independent reviewer is a person who did not author the work being approved and whose review is retained in a durable record. Where independent review is unavailable, the documented `SOLO_DEVELOPER_APPROVED_WORKAROUND` may be used for bounded founder verification. That compensating control is not independent review, self-approval, or production authorization.

## Review and evidence path

The controlled path may include:

- Founder/Product Owner direction and acceptance;
- exact-source and exact-head repository inspection;
- backend, frontend, tenant, permission, security, contract, and browser tests;
- CI and static-analysis results;
- retained runtime artifacts and evidence packets;
- AI-assisted findings that are explicitly identified as automated assistance;
- qualified human review where required by the RACI or release controls.

## Required verification areas

### Architecture and wiring

- module boundaries and dependency order are consistent;
- canonical data ownership is defined;
- backend services, APIs, frontend routes, and dashboard sources are connected;
- registry coverage or page rendering is not treated as completion.

### Security and tenancy

- tenant isolation is tested;
- action-level permissions are tested beyond page visibility;
- direct URL, export, redaction, sensitive-data, and audit behavior are covered;
- sensitive modules receive qualified human security review before certification.

### Quality and evidence

- models and migrations are verified where applicable;
- backend and frontend workflows are tested;
- runtime proof is current and tied to the exact evaluated SHA;
- screenshots, sample data, templates, and automated findings do not independently prove completion;
- blockers and limitations remain explicit.

### Product workflow

- school-operating workflows are coherent;
- persona access and outcomes are verified;
- dashboards identify source modules, provenance, freshness, drilldowns, and export rules;
- module completion precedes dashboard certification.

## Certification boundaries

A module or dashboard cannot be marked Certified unless all applicable requirements in the completion, ownership, permission, dashboard-fit, evidence, and review records are satisfied.

Certification does not create production approval. Production posture remains controlled exclusively by `docs/CURRENT_RELEASE_STATUS.md`, current-head release evidence, and an explicit Founder/Product Owner decision.

## Accepted review evidence

Review evidence may include:

- a GitHub pull-request review from an identified qualified person;
- a signed or attributable review memorandum;
- a committed review summary naming the reviewer and date;
- a security, QA, architecture, legal, or operational report with findings and dispositions;
- CI and automated-analysis output supporting, but not replacing, human review.

## Prohibited interpretations

This packet must never be used to claim that:

- an AI system or automated tool independently reviewed or approved CROWN;
- TC Megahan independently reviewed or approved his own authored work;
- a passing automated check alone certifies a module, dashboard, release, or production deployment;
- historical review language overrides current governance;
- production is approved without controlling current-head evidence and explicit authorization.

## Current outcome

The module and dashboard planning framework may be used for controlled evidence gathering. Individual module and dashboard status must be determined from current evidence. Production remains not approved unless and until the controlling release record states otherwise.
