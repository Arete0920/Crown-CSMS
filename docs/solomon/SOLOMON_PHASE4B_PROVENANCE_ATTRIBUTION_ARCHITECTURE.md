# SOLOMON Phase 4B: Provenance & Attribution Architecture

**Status:** ARCHITECTURE REVIEW COMPLETE (Design Approved, Implementation Pending)  
**Date:** 2026-05-29  
**Related:** Phase 4A Slice 3 (Governance Signal Detection)  
**Decision Gate:** Requires explicit approval before Phase 4B implementation begins

---

## Executive Summary

Phase 4B extends SOLOMON's governance observation capability by adding **provenance** (what happened, when, how) and **attribution** (who was responsible) tracking.

**Critical principle:** Provenance records and attribution metadata **inform** governance decisions; they do **not enforce** them.

**Authority preservation:** All governance decisions remain human-owned. Provenance and attribution are advisory telemetry, not enforcement mechanisms.

## 0. Human Review Outcome (S-101)

Review completed on 2026-05-29 with governance-first approval of the architecture boundary.

Accepted review decisions:
- Provenance remains append-only and non-mutating.
- Attribution remains accountability metadata and not an authorization channel.
- Canonical governance fields remain human-controlled only.
- Queryability remains read-only for analysis and audit.
- Automation remains deferred until post-4B maturity and separate approval.

Open questions requiring implementation-stage resolution:
- Which append-only storage option will be selected (single audit model vs partitioned event models)?
- Which retention and archival policy applies to long-lived provenance records?
- Which endpoint set is required for initial read-only provenance queries?
- Which minimal dashboard metric set is required for first release?
- Which migration/backfill approach will initialize provenance for pre-existing SOLOMON resources?

---

## Part 1: Core Definitions

### 1.1 Provenance in SOLOMON

**Definition:**
Provenance is the **immutable historical record** of what happened to a resource:
- When was it created?
- When was it modified?
- Which signal detected a change?
- What review queue action occurred?
- What state transition happened?
- Who initiated the review?

**Key characteristic:** Provenance is **append-only**. It records events; it never overwrites or deletes prior events.

**Scope (Phase 4B):**
- Resource creation timestamp (already exists via `created_at`)
- Resource update timestamp (already exists via `updated_at`)
- Signal detection events (new: which signal detected what, when)
- Review queue entries (new: when a resource entered/left review queue)
- Status change events (new: when lifecycle changed, by whom)
- Visibility change events (new: when visibility changed, by whom)

**Scope (NOT Phase 4B - defer to future):**
- Content change history (versioning; defer to Phase 5)
- Category/topic reassignments (relationship history; defer to Phase 5)
- User permission changes (access history; defer to Phase 6)
- Approval workflows (multi-step governance; defer to Phase 5)

### 1.2 Attribution in SOLOMON

**Definition:**
Attribution is the **verifiable association** of responsibility and accountability:
- Who created this resource?
- Who last modified it?
- Who triggered the current review?
- What system/service initiated an action?
- What user made a governance decision?

**Key characteristic:** Attribution records the **actor** (user or system) responsible for each action. It supports accountability without creating automatic authority.

**Scope (Phase 4B):**
- Resource creator (already exists via content metadata)
- Last modifier (already exists via content metadata)
- Signal detector identity (new: which signal detected what)
- Review queue initiator (new: who queued a resource for review)
- Status change actor (new: who changed the lifecycle state)
- Visibility change actor (new: who changed visibility)

**Scope (NOT Phase 4B - defer to future):**
- Approval chain (who approved, in what order)
- Rejection reasons (why a resource was rejected)
- Re-submission metadata (who resubmitted and why)
- Comments/annotations (defer to Phase 5)

### 1.3 Relationship Between Provenance and Attribution

| Aspect | Provenance | Attribution |
|---|---|---|
| **What** | Events and state changes | Actors and responsibility |
| **When** | Timestamps and sequencing | Actor identity with timestamp |
| **Why** | Audit trail, accountability, traceability | Governance transparency, human oversight |
| **Immutable?** | Yes (append-only) | Yes (records don't change, only new ones added) |
| **Enforcing?** | No (signals only) | No (records only, no auto-authority) |

---

## Part 2: Append-Only Principles

### 2.1 What Must Be Append-Only

✅ **Provenance audit log:**
- Signal detection events
- Status transition events
- Visibility change events
- Review queue entries
- *All are recorded, never edited or deleted*

✅ **Attribution records:**
- Who created each resource
- Who last modified each resource
- Who initiated each review action
- *Records are immutable once created*

✅ **Timestamps:**
- `created_at` (immutable)
- `updated_at` (only advances, never regresses)
- Signal detection timestamps (immutable)
- Review queue timestamps (immutable)

### 2.2 What Must NOT Be Retroactively Changed

❌ **Provenance records cannot be edited** (if a signal was wrong, create a new signal record, not a correction)  
❌ **Attribution records cannot be reassigned** (if actor was wrong, document the error, don't rewrite history)  
❌ **Timestamps cannot regress** (time moves forward only)  
❌ **Signal records cannot be deleted** (even if false positive, keep the record with context)  
❌ **Review queue history cannot be rewritten** (all queuing decisions are permanent records)

### 2.3 Append-Only Storage Strategy (Future Implementation Detail)

**Not decided in Phase 4B; relevant for Phase 4B implementation planning:**
- Option A: New `SolomonAuditLog` model (one row per event, never modified)
- Option B: New `SolomonProvenance` model with `SolomonProvenance.attribution_snapshot`
- Option C: JSON audit trail in existing resource (with versioning constraints)
- Option D: Separate append-only log service (distributed audit)

**Decision deferred to implementation phase.**

---

## Part 3: Queryability Rules

### 3.1 What May Be Queried

✅ **Provenance queries (read-only):**
- "What signals detected issues with resource X?"
- "When did resource X enter the review queue?"
- "What was the sequence of status changes for resource X?"
- "Which resources had visibility changes in the last 30 days?"
- "How long has resource X been in DRAFT state?"

✅ **Attribution queries (read-only):**
- "Who created resource X?"
- "Who last modified resource X?"
- "Who triggered the current review of resource X?"
- "What system/signal initiated this detection?"
- "Which resources were created by user Y?"

✅ **Combined queries (read-only):**
- "Show me all resources created by user X, with their current status and review queue age"
- "List all resources that have been in DRAFT for >72 hours, showing creation date and initiator"
- "Which resources had orphaned relationship detections, and who triggered those detections?"

### 3.2 What Must Never Be Queryable for Enforcement

❌ **Provenance queries must NOT drive automatic actions:**
- "If signal detected orphaned resource, auto-delete it" ← NO
- "If resource in review queue >72 hours, auto-approve" ← NO
- "If status changed 3 times, auto-archive" ← NO

❌ **Attribution queries must NOT create automatic authority:**
- "If resource created by user X, skip review" ← NO
- "If creator is admin, auto-publish" ← NO
- "If last modifier is staff, grant privileges" ← NO

### 3.3 Query Interface Design (Future Phase 4B Implementation)

**Not decided in Phase 4B; relevant for planning:**
- API endpoints for provenance queries
- Filtering by date range, signal type, status, actor
- Pagination for large result sets
- Caching strategy for read-heavy queries
- Rate limiting for audit log access

**Decision deferred to implementation phase.**

---

## Part 4: Canonical Resource Protection

### 4.1 Hard Boundary: Provenance Records Must Never Mutate Canonical Resources

**Canonical resources that must remain stable:**

| Resource Type | Protection |
|---|---|
| `SolomonResource.status` | Can only change via explicit human action (not provenance signal) |
| `SolomonResource.visibility` | Can only change via explicit human action (not provenance signal) |
| `SolomonResource.owner` | Can only change via explicit human action (not provenance signal) |
| `SolomonResource.approver` | Can only change via explicit human action (not provenance signal) |
| `SolomonResource.review_date` | Can only change via explicit human action (not provenance signal) |
| `SolomonPlaybook.status` | Can only change via explicit human action (not provenance signal) |
| `SolomonAudience.is_public` | Can only change via explicit human action (not provenance signal) |
| `SolomonCategory.is_public` | Can only change via explicit human action (not provenance signal) |

**Principle:** Provenance records and attribution metadata **observe** these resources; they **never modify** them.

### 4.2 What CAN Be Created by Provenance (New Records Only)

✅ **Provenance entries** (append-only log, not mutating canonical resources):
- "Signal X detected orphaned resource at timestamp Y"
- "Resource entered review queue at timestamp Y by user Z"
- "Status changed from DRAFT to APPROVED at timestamp Y by user Z"

✅ **Attribution snapshots** (read-only metadata):
- "Created by user X at timestamp Y"
- "Last modified by user X at timestamp Y"
- "Review initiated by user X at timestamp Y"

### 4.3 Separation of Concerns

**What Phase 4B observes (new):**
- When did signal detect an issue?
- Who triggered this action?
- What was the sequence of events?

**What Phase 4B does NOT touch (already working, must not break):**
- Status lifecycle (DRAFT → APPROVED → PUBLISHED → ARCHIVED)
- Visibility rules (PUBLIC, AUTHENTICATED, STAFF, ADMIN)
- Permission model (bearer token, role-based access)
- Resource content (title, summary, content fields)

---

## Part 5: Human Governance Preservation

### 5.1 Decisions That Remain Human-Owned

All of these require explicit human action and decision:

✅ **Lifecycle decisions:**
- Resource should transition from DRAFT to APPROVED
- Resource should transition from APPROVED to PUBLISHED
- Resource should be archived

✅ **Visibility decisions:**
- This resource should become PUBLIC
- This resource should be restricted to STAFF only
- This resource should be made ADMIN-only

✅ **Assignment decisions:**
- User X is now the owner of this resource
- User Y is now the approver of this resource
- Resource belongs in category Z

✅ **Governance decisions:**
- Resource needs to be re-reviewed
- Resource needs content updates
- Resource has been superseded by another

### 5.2 What Provenance Records Support (Advisory Only)

Provenance and attribution records **inform** human decision-makers:

- "This resource has been in review for 72+ hours" (advisory signal)
- "This resource was flagged as orphaned by signal X" (advisory signal)
- "User X has not reviewed this resource in 90 days" (advisory signal)
- "Resource was last modified by user Y on date Z" (contextual information)
- "This resource entered the queue on date Z" (contextual information)

**Governance process remains:**
1. System detects a condition (via signal)
2. System records the detection in provenance log (append-only)
3. Human reviews the advisory signal
4. Human makes a governance decision
5. Human action is recorded in provenance log
6. Process repeats

### 5.3 What Provenance Records Do NOT Do

❌ **Auto-approval** — "If flagged orphaned, auto-archive" ← NO  
❌ **Auto-escalation** — "If in review >72h, auto-notify" ← NO (notify, yes; auto-decide, no)  
❌ **Auto-reassignment** — "If owner inactive, auto-reassign" ← NO  
❌ **Auto-correction** — "If orphaned detected, auto-clean" ← NO  
❌ **Auto-expiration** — "If old enough, auto-archive" ← NO  

All governance decisions flow through human review, not provenance analysis.

---

## Part 6: Phase 4B Enforcement Constraints

### 6.1 Hard Boundary: Provenance/Attribution May NOT

❌ **Change resource status**
- No auto-draft, auto-approve, auto-publish, auto-archive

❌ **Change visibility**
- No auto-public, auto-staff, auto-admin based on provenance signals

❌ **Change ownership**
- No auto-reassignment to creator, last modifier, or any actor

❌ **Approve content**
- No auto-approval based on review history, creator role, or attribution

❌ **Archive content**
- No auto-archiving based on age, review count, or signal frequency

❌ **Assign responsibility**
- No auto-assignment of ownership/approver roles

❌ **Trigger notifications**
- No auto-alerts based on provenance patterns (human review first)

❌ **Auto-correct metadata**
- No auto-fixing of owner/approver/category based on history

❌ **Create enforcement policies**
- No provenance-triggered access control changes
- No attribution-driven permission modifications

### 6.2 What Phase 4B Can Do

✅ **Record events (append-only):**
- Signal detections
- Status changes
- Visibility changes
- Review queue movements

✅ **Record actors (attribution):**
- Who initiated actions
- Who made decisions
- System/service responsible

✅ **Support queries (read-only):**
- Historical analysis
- Audit trails
- Traceability

✅ **Support dashboards (advisory):**
- Health metrics
- Trend analysis
- Pattern identification

✅ **Generate alerts (advisory only):**
- "Resource in review >72 hours" (human decides action)
- "Signal detected orphaned resource" (human decides action)
- "Visibility has changed 3x in 30 days" (human decides action)

---

## Part 7: Phase 4B Scope Definition

### 7.1 What Phase 4B Will Implement

When Phase 4B is approved and implementation begins:

1. **Provenance Recording:**
   - Append-only log model/table for signal detection events
   - Append-only log model/table for governance action events
   - Timestamp and actor capture for each event
   - No retroactive modifications allowed

2. **Attribution Metadata:**
   - Actor identity recording (user or system)
   - Action timestamp recording
   - Signal/service identity for automated signals
   - Human user identity for manual actions

3. **Query APIs:**
   - Provenance lookup (read-only)
   - Attribution lookup (read-only)
   - Event history retrieval
   - Timeline and sequence queries

4. **Dashboard Support:**
   - Governance health visualization
   - Resource age and review time metrics
   - Signal detection patterns
   - Actor activity summaries

### 7.2 What Phase 4B Will NOT Implement

Explicitly deferred to future phases:

❌ **Version history** (defer to Phase 5 — Content Versioning)
- We track *that* something changed, not *what* changed in detail
- Full content versioning deferred

❌ **Approval workflows** (defer to Phase 5 — Multi-Step Governance)
- We track signal detections and human actions
- Complex approval chains deferred

❌ **Comments and annotations** (defer to Phase 5 — Governance Collaboration)
- We track actor identity, not collaboration history
- Comment threads deferred

❌ **Change reasons/justifications** (defer to Phase 5 — Governance Context)
- We track that an actor changed something, not why
- Reasoning capture deferred

❌ **Role-based provenance filtering** (defer to Phase 6 — Access Control)
- All provenance is queryable by authorized users
- Role-specific views deferred

❌ **Automated reporting** (defer to Phase 6 — Governance Automation)
- Dashboards and queries are on-demand
- Scheduled reports deferred

❌ **Data retention policies** (defer to Phase 7 — Compliance)
- We keep all provenance records
- Retention policies deferred

---

## Part 8: Architecture Decision Record

### 8.1 Core Decisions Made

**Decision 1: Provenance is append-only, never modified**
- **Rationale:** Immutability ensures audit trail integrity
- **Implication:** Wrong signals create new records, not corrections
- **Impact:** Supports accountability and traceability

**Decision 2: Attribution supports accountability, not automatic authority**
- **Rationale:** Human governance remains the authority
- **Implication:** Knowing who acted doesn't auto-execute actions
- **Impact:** Prevents hidden automation coupling

**Decision 3: Provenance records inform; they do not enforce**
- **Rationale:** Governance decisions must remain human-owned
- **Implication:** No provenance-triggered auto-mutations
- **Impact:** Preserves human governance authority

**Decision 4: Canonical resources remain stable**
- **Rationale:** Status, visibility, ownership are governance decisions
- **Implication:** Provenance records never change these fields
- **Impact:** Separation of observation from governance

**Decision 5: All decisions remain reversible by humans**
- **Rationale:** Provenance shows what happened; humans decide what's next
- **Implication:** No cascading side effects from provenance analysis
- **Impact:** Human can always override and correct

### 8.2 Constraints Enforced in Code

**During Phase 4B implementation, enforce these invariants:**

```
INVARIANT: No SolomonResource.status change without explicit human action
INVARIANT: No SolomonResource.visibility change without explicit human action
INVARIANT: No SolomonResource.owner change without explicit human action
INVARIANT: No SolomonResource.approver change without explicit human action
INVARIANT: Provenance records are append-only (never UPDATE or DELETE)
INVARIANT: Attribution records are immutable (created once, never modified)
INVARIANT: All provenance timestamps are ISO-8601 and UTC
INVARIANT: All provenance actors are either user.id or system service identity
INVARIANT: All provenance events are queryable by authorized users
INVARIANT: No provenance record triggers an automatic state change
```

---

## Part 9: Future Phases Preview (Not Phase 4B)

### 9.1 Phase 4C: Governance Automation (Future)

After Phase 4B is stable and reviewed:

**Potential Phase 4C scope:**
- Workflow automation (multi-step approval chains)
- SLA enforcement (resources must be reviewed by deadline)
- Escalation policies (notify if review delayed)
- Template management (reusable governance patterns)

**Hard constraint:** All Phase 4C automation must be:
1. **Explicitly enabled** (not implicit, opt-in)
2. **Auditable** (all actions logged via provenance)
3. **Reversible** (humans can undo automated actions)
4. **Bounded** (cannot cascade beyond immediate scope)

### 9.2 Phase 5: Content Versioning (Future)

Track what changed in resource content, not just when/who:

**Scope (Future):**
- Full version history of content
- Diff tracking for changes
- Reversion capability
- Change reason capture

### 9.3 Phase 6: Access Control (Future)

Extend provenance to access and permission changes:

**Scope (Future):**
- Permission change history
- User role change tracking
- Access grant/revoke audit
- Delegation tracking

---

## Part 10: Review Checklist

Before Phase 4B implementation begins, answer these questions:

- [ ] Does the team agree that provenance records **inform** but do not **enforce**?
- [ ] Does the team agree that all governance decisions remain **human-owned**?
- [ ] Does the team agree that canonical resources (status, visibility, owner) are **stable**?
- [ ] Does the team agree that provenance records are **append-only and immutable**?
- [ ] Does the team agree to **defer** content versioning to Phase 5?
- [ ] Does the team agree to **defer** approval workflows to Phase 5?
- [ ] Does the team agree to **defer** access control provenance to Phase 6?
- [ ] Does the team agree that no provenance signal may auto-mutate governance state?
- [ ] Does the team agree that attribution supports accountability, not automation?
- [ ] Does the architecture align with bearer-token security model (no role-based auto-execution)?

---

## Part 11: Implementation Readiness

**Status:** REVIEW APPROVED / PENDING IMPLEMENTATION  

When this document is explicitly approved, Phase 4B implementation can begin with:

1. **Provenance model design** (append-only log schema)
2. **Attribution capture** (actor identity recording)
3. **Query API design** (read-only endpoints)
4. **Test suite** (provenance immutability verification)
5. **Dashboard** (advisory visualization only)

**Implementation must NOT begin** until:
- [ ] This architecture document is reviewed
- [ ] All decisions are explicitly approved
- [ ] No changes to hard boundaries without re-review
- [ ] Team commits to human governance preservation

---

## Sign-Off

**Architecture Review Status:** APPROVED (2026-05-29)

This document establishes the boundaries and principles for Phase 4B.

**Next step:** Begin implementation design only within the approved boundaries and open-question controls.

---

**Document Version:** 1.1  
**Last Updated:** 2026-05-29  
**Related Commits:** e54ccad9 (Phase 4A Slice 3)
