# CROWN ARCHITECTURE CANON

> **Legacy Positioning Note**
>
> This file contains older Crown Compass / Crown Solomon / Crown Discernment positioning language.
> The current authoritative definitions are:
> - `docs/canon/CROWN_COMPASS_CANON.md`
> - `docs/canon/CROWN_SOLOMON_CANON.md`
> - `docs/canon/CROWN_DISCERNMENT_PRINCIPLES.md`
> - `docs/canon/CROWN_DISCERNMENT_TECHNICAL_POSITION.md`
> - `docs/canon/CROWN_COMPASS_SOLOMON_DISCERNMENT_ARCHITECTURE.md`
>
> Until runtime implementation is explicitly approved, predictive analytics and scenario modeling remain conceptual and must not be treated as production-integrated features.

**Version:** 1.0
**Status:** Frozen Governance Document
**Authority:** Platform Doctrine

---

## 1. Purpose

This document defines the permanent architectural structure, module boundaries, design discipline, and governance guardrails for the Crown platform ecosystem.

**No module, feature, or UI change may violate this canon.**

---

## 2. Ecosystem Structure

### 2.1 Crown (Core Platform)

**Purpose:** Operational backbone for Christian schools.

**Owns:**
- Admissions
- Enrollment
- Billing
- Financial Aid
- Academics
- Attendance
- Communications
- Dashboard framework
- Permission engine
- Tenant enforcement
- Audit logging

Crown is infrastructure.
All modules sit on Crown.

---

### 2.2 Crown Compass (Leadership & Strategy Add-on)

**Purpose:** Leadership, board, governance, mission-alignment, institutional health, and scenario-support add-on for Crown.

**Provides:**
- executive and board visibility
- mission-aligned institutional reporting
- governance-ready summaries
- trend and scenario review within approved constraints
- leadership-facing strategic insight
- Discernment-powered outputs only when explicitly approved and implemented as transparent, auditable, human-support tooling

Crown Compass is a Crown Add-on.
It is not Crown Core and not the system of record.

**Compass does not:**
- own student, household, attendance, billing, or transcript truth
- replace leadership judgment, pastoral care, or board governance
- operate as a black-box or autonomous decision-maker
- imply production-ready predictive integration before canon and governance approval

---

### 2.3 Barnabas (Mentoring & Guidance System)

*Inspired by Barnabas*

**Purpose:** Human formation and encouragement system.

**Owns:**
- Daily devotions
- Student reflection prompts
- Parent encouragement prompts
- Spiritual milestone tracking
- Mentor journaling
- Formation pathways

**Barnabas does not:**
- Perform financial analytics
- Modify tuition data
- Operate admissions logic

Barnabas is formation-centered, not KPI-centered.

---

### 2.4 Solomon (Guidance, Governance & Enablement Layer)

**Purpose:** Mission-aware knowledge, onboarding, governance-template, interpretation, and playbook support for the Crown ecosystem.

**Owns:**
- governance templates
- policy documents
- board education resources
- implementation guidance
- best-practice research
- leadership interpretation content
- next-step and playbook resources

**Solomon does not:**
- serve as the predictive analytics engine
- execute autonomous recommendations
- replace school leadership or board judgment
- modify operational records as a system of record

---

### 2.5 Operation Andrew (Admissions Referral Module)

*Inspired by Andrew*

Lives within **Crown → Admissions**.

**Model:** Hybrid tuition credit + scholarship give-back.

**Owns:**
- Referral code generation
- Referral attribution tracking
- Reward qualification logic
- Tuition credit issuance
- Scholarship give-back option
- Referral dashboard metrics

Operation Andrew integrates with Compass for ROI measurement.

---

## 3. Architectural Guardrails

### 3.1 One Design System

The platform shall maintain:
- One CSS variable system
- One spacing scale
- One button component system
- One card component system
- One table component system
- One chart library
- No inline hex colors
- No duplicated UI patterns

Sub-modules may adjust accent tones but may not create independent UI systems.

### 3.2 One Permission Engine

- Single permission registry
- All endpoints enforce permission checks
- Navigation derived from permissions
- No module bypass
- All future features integrate into the same enforcement framework

### 3.3 One Tenant Model

- All modules enforce tenant isolation
- All data access must respect `request.school`
- No cross-tenant access allowed
- No demo shortcuts bypassing tenant enforcement

### 3.4 Layer C Scoping Doctrine

Row and field scoping must:
- Be centralized
- Be role-defined
- Be test-covered
- Be contract-frozen before module expansion
- Not rely on scattered queryset filtering

### 3.5 Demo Integrity Doctrine

Demo Mode must:
- Be environment-gated
- Never default to enabled
- Never expose plaintext credentials
- Never bypass permission logic
- Use seeded canonical demo tenant (Heritage)

---

## 4. Module Boundaries Matrix

| System | Data Ownership | Analytics | Formation | Admissions | Governance |
|--------|---------------|-----------|-----------|------------|------------|
| Crown | Yes | Limited | No | Yes | Limited |
| Crown Compass | No (consumes governed truth) | Yes (transparent / parameter-bound, add-on only) | No | No | Yes |
| Barnabas | Limited | No | Yes | No | No |
| Solomon | No | No | Guidance / Advisory | No | Yes (templates / interpretation) |
| Operation Andrew | Admissions-linked | Yes (ROI) | Encouragement tone | Yes | No |

---

## 5. Roadmap Order (Frozen)

1. Core Stabilization
2. Layer C Implementation
3. Design Canon Lock
4. Barnabas v1
5. Operation Andrew
6. Crown Compass canon alignment and add-on planning
7. Crown Solomon guidance alignment

**Predictive analytics / Discernment work is later-phase, canon-gated, and not approved for production integration in this roadmap.**

---

## 6. What Is Prohibited

- Independent sub-brand UI systems
- Permission bypass logic
- Tenant isolation shortcuts
- Inline styling that violates canon
- Demo-only hacks in production code
- Feature expansion without canon alignment

---

## 7. Governance Enforcement

All pull requests must:
- Pass full backend test suite
- Respect permission engine
- Respect tenant isolation
- Follow visual canon
- Avoid duplication of components
- Avoid introduction of ungoverned modules

---

## 8. Canon Amendment Process

Any architectural change requires:
- Explicit review
- Canon update
- Documentation revision
- Test coverage updates

**No silent drift permitted.**

---

*End of Canon v1*
