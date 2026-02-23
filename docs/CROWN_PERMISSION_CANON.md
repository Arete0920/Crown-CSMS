# CROWN PERMISSION CANON

**Version:** 1.0
**Status:** Frozen Governance Doctrine
**Authority:** Security & Access Control Standard

---

## 1. Purpose

This document defines the permanent access control model for the Crown ecosystem.

It governs:
- Role definitions
- Permission naming standards
- Endpoint enforcement rules
- Navigation derivation
- Row and field scoping (Layer C)
- Audit requirements

**No module may bypass this canon.**

---

## 2. Access Control Architecture

Crown enforces four layers of access control:

1. **Authentication** (identity)
2. **Permission-based authorization** (role capability)
3. **Tenant isolation** (school boundary)
4. **Row and field scoping** (data visibility control)

**All four layers must remain active at all times.**

---

## 3. Role Doctrine

### 3.1 Canonical Roles

Core roles (expandable but standardized):

- Super Admin
- School Director / Head of School
- Board Member
- Finance Officer
- Registrar
- Admissions Officer
- Teacher
- Counselor
- Parent
- Student
- IT Admin
- Advancement Officer
- Spiritual Life Director
- Support Staff

Role names must remain consistent across modules.
**No module-specific role silos permitted.**

---

## 4. Permission Naming Standard

All permissions must follow:

```
<domain>.<action>
```

**Examples:**

```
students.view
students.edit
billing.view
billing.manage
aid.award
referrals.create
devotions.publish
mentor.view
compass.score_view
```

**Rules:**
- Lowercase only
- Dot-separated
- No camelCase
- No role-specific permission names
- No duplicate semantic permissions

---

## 5. Enforcement Rules

### 5.1 Endpoint Enforcement

Every API endpoint must:
- Require authentication
- Require explicit permission check
- Enforce tenant isolation
- Apply row scoping if applicable

**No endpoint may rely on frontend hiding alone.**

### 5.2 Navigation Enforcement

Navigation must:
- Be derived from permission checks
- Never hardcode role-based visibility
- Hide modules entirely if permission absent

---

## 6. Tenant Isolation Doctrine

All requests must:
- Validate `request.school`
- Reject cross-tenant access
- Return `403` or `404` appropriately

**Tenant logic must never be optional.**

---

## 7. Layer C — Row & Field Scoping Doctrine

Layer C governs what records and fields a user may see.

### 7.1 Row Scoping

Row visibility must be centralized.

**Examples:**
- Teacher → only students in assigned sections
- Parent → only their children
- Student → only their own record
- Counselor → only assigned students
- Finance → all financial records, not counseling notes

Row scoping must:
- Be defined in a centralized scoping module
- Be applied before serialization
- Be test-covered
- Not be duplicated in views

**No scattered queryset filtering permitted.**

### 7.2 Field Scoping

Field visibility must:
- Be role-based
- Be defined in serializer logic or scoping layer
- Prevent sensitive leakage

**Examples:**
- Finance sees balances, not discipline notes
- Counselor sees notes, not donor giving
- Parent sees grades, not internal staff comments

Field scoping must:
- Be explicit
- Be documented
- Be test-covered

---

## 8. Demo Mode Restrictions

Demo Mode must:
- Never bypass permission checks
- Never disable tenant enforcement
- Never expose hidden fields
- Only alter authentication flow

**Demo is visibility convenience, not privilege escalation.**

---

## 9. Operation Andrew Permission Structure

Operation Andrew permissions:

```
referrals.view
referrals.create
referrals.manage
referrals.reward_issue
```

Referral rewards must:
- Respect finance permissions
- Log audit entries
- Require authorized role

---

## 10. Barnabas Permissions

Barnabas permissions:

```
devotions.view
devotions.publish
mentor.view
mentor.log_entry
formation.track
```

Barnabas must:
- Respect student privacy
- Respect counselor boundaries
- Enforce parent visibility limits

---

## 11. Compass Permissions

Compass permissions:

```
compass.view
compass.score_view
compass.admin
```

**Compass is read-only relative to operational data.**

---

## 12. Audit & Test Requirements

Every permission-sensitive change must include:
- Unit tests for permission checks
- Row scope validation tests
- Field scope validation tests
- Tenant boundary test

**No permission change may merge without coverage.**

---

## 13. Prohibited Patterns

The following are prohibited:
- Checking role string directly in views
- Inline permission logic scattered across modules
- UI-only hiding of restricted features
- Returning entire object then filtering in frontend
- Disabling tenant middleware in production

---

## 14. Canon Amendment Protocol

Permission model changes require:
- Canon update
- Documentation revision
- Test update
- Code review confirmation

**No silent expansion of privilege.**

---

*Permission Canon v1 Locked*
