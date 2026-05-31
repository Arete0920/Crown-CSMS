# CROWN Printed Binder Mermaid Visuals — 2026-05-29

## Purpose

This document provides binder-ready visual diagrams for CROWN using Mermaid. These diagrams are intended for printed executive, architect, investor, school-leader, and release-authority binders.

## Current certification note

These visuals describe the intended and governed architecture. They do **not** certify CROWN as GA, pilot-approved, unrestricted-production ready, or superior-certified. Current release authority remains controlled by the release gates and evidence artifacts.

## Printing guidance

Recommended binder use:

1. Open this Markdown file in GitHub or a Mermaid-capable Markdown viewer.
2. Let Mermaid render the diagrams.
3. Print to PDF or paper from the rendered preview.
4. Use landscape orientation for the larger system maps.
5. Keep this file paired with:
   - `docs/release/CROWN_RELEASE_AUTHORITY_INDEX_20260529.md`
   - `docs/release/CROWN_CORE_SIS_SUPERIORITY_GATE_20260529.md`
   - `docs/release/CROWN_OWNER_RUNTIME_PROOF_ACTION_PACKET_20260529.md`

---

# 1. Executive System Map

```mermaid
flowchart TB
    CROWN[CROWN\nChristian School Management Solution]

    CROWN --> SIS[Core SIS]
    CROWN --> FIN[Finance and Billing]
    CROWN --> FAMILY[Family Engagement]
    CROWN --> OPS[School Operations]
    CROWN --> MISSION[Mission and Formation]
    CROWN --> PLATFORM[Platform Governance]

    SIS --> STUDENTS[Students]
    SIS --> HOUSEHOLDS[Households and Guardians]
    SIS --> ATTENDANCE[Attendance]
    SIS --> SCHEDULING[Scheduling]
    SIS --> GRADEBOOK[Gradebook]
    SIS --> REGISTRAR[Registrar and Transcripts]

    FIN --> TUITION[Tuition Plans]
    FIN --> INVOICES[Invoices]
    FIN --> PAYMENTS[Payments]
    FIN --> AID[Financial Aid]
    FIN --> LEDGER[Ledger and Reconciliation]

    FAMILY --> PORTALS[Parent and Student Portals]
    FAMILY --> COMMS[Communications]
    FAMILY --> ADMISSIONS[Admissions and Enrollment]
    FAMILY --> REENROLL[Re-enrollment]

    OPS --> HR[HR and Staff]
    OPS --> FACILITIES[Facilities]
    OPS --> HEALTH[Health Office]
    OPS --> TRANSPORT[Transportation]
    OPS --> FOOD[Food Service]
    OPS --> SAFETY[Safety and Security]

    MISSION --> SPIRITUAL[Spiritual Life]
    MISSION --> SERVICE[Service Hours]
    MISSION --> CARE[Student Care]
    MISSION --> ADVANCEMENT[Advancement and Alumni]

    PLATFORM --> TENANT[Tenant Isolation]
    PLATFORM --> RBAC[RBAC and Object Authorization]
    PLATFORM --> DASH[Dashboard Provenance]
    PLATFORM --> RELEASE[Release Authority Gates]
    PLATFORM --> OBS[Observability and Incident Readiness]
```

---

# 2. Core SIS Operating Flow

```mermaid
flowchart LR
    A[Admissions Inquiry] --> B[Application]
    B --> C[Human Review]
    C --> D{Decision}
    D -->|Accepted| E[Enrollment Conversion]
    D -->|Waitlist| W[Waitlist Management]
    D -->|Declined| X[Closed Application]

    E --> F[Student Record]
    E --> G[Household and Guardians]
    E --> H[Billing Account]
    E --> I[Portal Access]

    F --> J[Scheduling]
    F --> K[Attendance]
    F --> L[Gradebook]
    F --> M[Student Care]
    F --> N[Registrar]

    J --> O[Class Rosters]
    K --> P[Attendance Reports]
    L --> Q[Report Cards]
    N --> R[Transcript]

    H --> S[Invoice]
    S --> T[Payment]
    T --> U[Ledger Reconciliation]
```

---

# 3. Tenant, RBAC, and Object-Authorization Flow

```mermaid
flowchart TB
    USER[User Request] --> AUTH[Authentication]
    AUTH --> TOKEN[Token / Session Claims]
    TOKEN --> TENANT[Tenant Resolution]
    TENANT --> RBAC[Role-Based Access Check]
    RBAC --> OBJECT[Object-Level Authorization]
    OBJECT --> API[API / Service Layer]
    API --> DATA[(Tenant-Scoped Data Store)]
    DATA --> RESPONSE[Response]

    TENANT -->|Missing or invalid tenant| DENY1[Deny]
    RBAC -->|Role not permitted| DENY2[Deny]
    OBJECT -->|Object outside scope| DENY3[Deny]

    RESPONSE --> AUDIT[Audit Log]
    DENY1 --> AUDIT
    DENY2 --> AUDIT
    DENY3 --> AUDIT
```

---

# 4. Dashboard Data Provenance Flow

```mermaid
flowchart LR
    W[Dashboard Widget] --> P{Provenance Complete?}
    P -->|No| BLOCK[Block Certification]
    P -->|Yes| DS{Data State}

    DS -->|Live| SRC[Backend Service / API]
    DS -->|Sandbox| SB[Clearly Labeled Sandbox]
    DS -->|Sample| SAMPLE[Not Certifiable]
    DS -->|Fallback| FALLBACK[Not Certifiable]
    DS -->|Unknown| UNKNOWN[Not Certifiable]

    SRC --> T[Prove Tenant Filter]
    T --> R[Prove Role Scope]
    R --> F[Prove Freshness]
    F --> E[Evidence Artifact]
    E --> CERT[Eligible for Dashboard Certification]

    SB --> CONTEXT[Deployment Context Review]
    CONTEXT -->|Sandbox Accepted| E
    CONTEXT -->|Production Claim| BLOCK

    SAMPLE --> BLOCK
    FALLBACK --> BLOCK
    UNKNOWN --> BLOCK
```

---

# 5. Release Authority Gate Stack

```mermaid
flowchart TB
    START[Release Candidate Branch] --> STACK[Run Release Authority Stack]

    STACK --> G106[106 Full-Completion Truth Gate]
    STACK --> G121[121 Dashboard Provenance Gate]
    STACK --> G122[122 Domain Model Certification Gate]
    STACK --> G130[130 Data Migration Reconciliation Gate]
    STACK --> G140[140 Financial Controls Gate]
    STACK --> G150[150 Performance Load Gate]
    STACK --> G160[160 Observability and Incident Gate]
    STACK --> G105[105 Dashboard Module Completion Gate]
    STACK --> G120[120 Release Authority Meta Gate]

    G106 --> STATUS[Status JSONs and Summaries]
    G121 --> STATUS
    G122 --> STATUS
    G130 --> STATUS
    G140 --> STATUS
    G150 --> STATUS
    G160 --> STATUS
    G105 --> STATUS
    G120 --> STATUS

    STATUS --> DECISION{All Required Evidence Green?}
    DECISION -->|No| NOGO[NO-GO / Integrity Hold]
    DECISION -->|Yes| SIGNOFF[Founder and Release Signoff]
    SIGNOFF --> GO[GO Decision for Approved Scope]
```

---

# 6. Evidence Binder Artifact Map

```mermaid
flowchart TB
    BINDER[Printed Binder]

    BINDER --> ARCH[Architecture Section]
    BINDER --> SIS[Core SIS Section]
    BINDER --> SECURITY[Security and Tenant Section]
    BINDER --> DASH[Dashboard Truth Section]
    BINDER --> RELEASE[Release Authority Section]
    BINDER --> OPS[Operations Section]
    BINDER --> SIGN[Signoff Section]

    ARCH --> A1[CROWN System Architecture]
    ARCH --> A2[Module Map]
    ARCH --> A3[Wiring / Plumbing Flow]

    SIS --> S1[Domain Model Certification]
    SIS --> S2[Workflow Proof Register]
    SIS --> S3[Wizard Proof Register]

    SECURITY --> SE1[Tenant Isolation Evidence]
    SECURITY --> SE2[RBAC Evidence]
    SECURITY --> SE3[Object Authorization Evidence]

    DASH --> D1[Dashboard Provenance Contract]
    DASH --> D2[Widget Provenance CSV]
    DASH --> D3[Sample / Fallback Violation Report]

    RELEASE --> R1[Release Authority Index]
    RELEASE --> R2[Gate Stack Summary]
    RELEASE --> R3[Blocking Markers Report]

    OPS --> O1[Backup / Restore Evidence]
    OPS --> O2[Incident Readiness Evidence]
    OPS --> O3[Go-Live Runbook]

    SIGN --> F1[Founder Signoff]
    SIGN --> L1[Legal / Compliance Approval]
    SIGN --> C1[Customer / Pilot Acceptance]
```

---

# 7. Pilot and Go-Live Sequence

```mermaid
sequenceDiagram
    participant Owner as Founder / Product Owner
    participant Repo as GitHub Repo
    participant CI as CI Gate Stack
    participant Runtime as Runtime Environment
    participant School as Pilot School
    participant Binder as Evidence Binder

    Owner->>Repo: Select release branch and commit
    Repo->>CI: Run release-authority workflow
    CI->>Binder: Emit .crown-audit evidence
    CI-->>Owner: Report PASS / REVIEW REQUIRED

    alt Gates fail
        Owner->>Repo: Remediate blockers
        Repo->>CI: Re-run gates
    else Gates green
        Owner->>Runtime: Execute runtime validation
        Runtime->>Binder: Attach screenshots, logs, proof outputs
        Owner->>School: Confirm pilot scope and acceptance criteria
        School-->>Owner: Accept or reject pilot entry
        Owner->>Binder: Attach signed approval
    end
```

---

# 8. Current Blocker Resolution Flow

```mermaid
flowchart TD
    OPEN[Open Release Work] --> CI[CI and Gate Results]
    CI --> FAILURES[Failure Diagnostics]

    FAILURES --> P1[Dashboard Preview / Provenance Blockers]
    FAILURES --> P2[Backend / Pytest / Schema Blockers]
    FAILURES --> P3[Wizard End-to-End Proof]
    FAILURES --> P4[Later-Tier Runtime Proof]
    FAILURES --> P5[Compliance / Customer Readiness]
    FAILURES --> P6[Founder / Customer Signoff]

    P1 --> FIX[Patch / Implement / Prove]
    P2 --> FIX
    P3 --> FIX
    P4 --> FIX
    P5 --> OWNER[Authorized Owner Evidence]
    P6 --> OWNER

    FIX --> RERUN[Re-run Gate Stack]
    OWNER --> RERUN
    RERUN --> DECISION{All Green?}
    DECISION -->|No| FAILURES
    DECISION -->|Yes| RELEASE_SIGNOFF[Final Release Authority Signoff]
```

---

# 9. Competitive Superiority Proof Flow

```mermaid
flowchart LR
    COMP[25 Competitor Matrix] --> LANES[Critical Market Lanes]

    LANES --> SISLANE[Core SIS]
    LANES --> FINLANE[Finance / Tuition]
    LANES --> UXLANE[UX / Workflow Efficiency]
    LANES --> SECLANE[Security / Tenant Safety]
    LANES --> MISSLANE[Christian Mission Fit]
    LANES --> IMPLANE[Implementation Readiness]

    SISLANE --> EVIDENCE[Evidence Required]
    FINLANE --> EVIDENCE
    UXLANE --> EVIDENCE
    SECLANE --> EVIDENCE
    MISSLANE --> EVIDENCE
    IMPLANE --> EVIDENCE

    EVIDENCE --> SCORE{Equal or Better in Every Critical Lane?}
    SCORE -->|No| NOCLAIM[No Superiority Claim]
    SCORE -->|Yes| CERT[Superiority Certification Candidate]
    CERT --> SIGN[Founder / Release Authority Signoff]
```

---

# 10. Binder Status Legend

```mermaid
flowchart LR
    GREEN[Green / PASS] --> CLAIM[May support scoped claim]
    YELLOW[Review Required] --> WORK[Needs inspection or remediation]
    RED[Blocked / NO-GO] --> HOLD[Release claim prohibited]
    BLUE[Documented Only] --> PROOF[Policy exists but runtime/signoff proof still required]
```

## Final binder note

Use these visuals as a map of CROWN's intended and governed architecture. Use the `.crown-audit` evidence outputs and signed release authority files as the proof source for whether a claim is allowed.
