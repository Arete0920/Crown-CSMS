# CROWN ARCHITECTURE CANON

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

### 2.2 Compass (Institutional Health & Sustainability)

**Purpose:** Institutional analytics and sustainability scoring engine.

**Owns:**
- Enrollment health metrics
- Retention analysis
- Financial sustainability ratios
- Referral ROI
- Aid-to-tuition ratio
- Risk indicators
- Institutional health scoring

Compass measures institutional strength.

**Compass does not:**
- Manage devotions
- Manage mentoring content
- Modify operational data

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

### 2.4 Solomon (Knowledge & Governance Library)

**Purpose:** Wisdom and governance repository.

**Owns:**
- Governance templates
- Policy documents
- Board training materials
- Best-practice research
- Leadership content

**Solomon does not:**
- Access live student data
- Modify operational records

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
| Compass | Read-only | Yes | No | No | No |
| Barnabas | Limited | No | Yes | No | No |
| Solomon | No | No | Advisory | No | Yes |
| Operation Andrew | Admissions-linked | Yes (ROI) | Encouragement tone | Yes | No |

---

## 5. Roadmap Order (Frozen)

1. Core Stabilization
2. Layer C Implementation
3. Design Canon Lock
4. Barnabas v1
5. Operation Andrew
6. Compass Activation
7. Solomon Integration

**No parallel module expansion outside this order.**

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
