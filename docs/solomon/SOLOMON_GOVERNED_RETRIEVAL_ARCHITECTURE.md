# CROWN Solomon Governed Retrieval Architecture

**Status:** Foundation implemented; retrieval remains disabled  
**Date:** 2026-10-06  
**Scope:** Provider-neutral governance and routing contracts only

## Purpose

This document defines the CROWN Solomon architecture for future retrieval-augmented guidance.

The design applies the useful engineering lessons from real-time RAG architecture without adopting an additional streaming platform. CROWN already has PostgreSQL, Redis, Celery, tenant middleware, RBAC, audit logging, and the Solomon C1 governance control plane. Those components remain the preferred foundation until measured scale demonstrates a need for additional infrastructure.

## Non-negotiable boundary

Solomon remains a knowledge, guidance, onboarding, governance-template, interpretation, and success-enablement layer.

Solomon is not:
- the CROWN system of record
- a substitute for school leadership
- an autonomous decision engine
- an authorization mechanism
- a route around tenant or role controls

No work in this architecture activates external generation, real ingestion, vector indexing, embedding generation, or retrieval.

## Routing model

Every future Solomon request must be classified before any retrieval occurs.

| Intent | Required route |
| --- | --- |
| Canonical guidance and approved unstructured knowledge | Cache, then governed corpus retrieval |
| Transactional student/family/finance/attendance/grade facts | Authorized structured CROWN service only |
| Aggregate analysis | Structured service first, then governed explanatory corpus only after separate aggregate-disclosure approval |
| Unknown or unsupported intent | Abstain |

Transactional records must never be vectorized merely to make them available to a language interface.

## Retrieval source eligibility

A source is not eligible merely because it exists in CROWN or is published.

Each retrievable source must have:
- stable source ID
- source title
- SHA-256 source digest
- source version
- approved provenance tier (P0-P2)
- approved review status
- explicit rights status and documented rights basis
- privacy classification
- tenant scope
- optional role scope
- effective/expiry dates where applicable
- human review date
- supersession metadata where applicable; superseded sources are rejected

The machine-readable contract is:
`solomon_governance_c1/governance/c1/schemas/retrieval_source.schema.json`.

## Data classes

### Suitable for governed semantic retrieval

Examples:
- approved help articles
- implementation guides
- policy templates
- onboarding instructions
- governance resources
- board education material
- operating procedures
- approved internal reference documents

### Structured-service only

Examples:
- student records
- parent/guardian records
- balances
- transactions
- attendance
- grades
- financial-aid records
- discipline records
- health information
- credentials
- identifiers

## Source authority

Retrieval must fail closed if a source:
- lacks an approved review status
- lacks approved rights
- has prohibited privacy classification
- is outside the active tenant
- is outside the caller role scope
- is expired or not yet effective
- lacks a valid source digest
- lacks a human review date
- has an unapproved provenance tier

A source may be globally scoped only when governance explicitly declares it global.

## Answer Authority Gate

Retrieved or synthesized output must not be returned merely because retrieval succeeded.

Before release, the response must pass an authority gate that verifies:
- at least one valid evidence source exists
- citations/source references are present
- tenant and role scope remain valid
- no prohibited or restricted data was detected
- unsupported factual claims were not detected
- consequential decision domains remain human-owned
- required human-review acknowledgement is satisfied

Failure results in **ABSTAIN**. Where only human acknowledgement is missing, the result is **HUMAN_REVIEW** rather than silent continuation.

The initial provider-neutral implementation is:
`backend/solomon/retrieval.py`.

## Consequential domains

Solomon must not autonomously make or release consequential decisions in:
- admissions
- grading
- discipline
- financial aid
- health
- safeguarding
- pastoral matters

Guidance may explain approved policy or process. The decision remains with authorized people and existing CROWN workflows.

## Caching

Repeated approved guidance may be cached after retrieval is eventually activated.

Cache keys must bind:
- tenant
- role
- topic
- corpus version
- policy version
- normalized question content protected by a keyed digest

Raw question text must not be stored in the cache key. Cache identifiers use a keyed digest so low-entropy or predictable questions cannot be recovered by simple offline guessing against an unkeyed hash.

Any corpus or policy version change naturally creates a new cache namespace and prevents stale answers from being reused under the old evidence state.

## Ingestion and indexing

The existing Solomon C1 control plane remains authoritative.

The repository currently supports deterministic governance simulation and explicitly blocks the deprecated real-ingestion entrypoint. That boundary remains unchanged.

Future activation sequence:

1. candidate source intake
2. provenance/rights/privacy review
3. canonical human approval
4. deterministic source digest
5. deterministic chunking
6. inherited provenance metadata
7. non-production indexing
8. retrieval evaluation
9. negative tenant/privacy/injection testing
10. authority-gate testing
11. exact-head CI evidence
12. explicit human release decision
13. production activation through a separately reviewed adapter

No stage may infer approval from a previous stage.

## Event-driven freshness

CROWN does not need an additional enterprise streaming platform to implement the first production version.

Preferred initial pattern:

```
Approved source change
    -> durable CROWN event/task
    -> Celery worker
    -> validate source governance
    -> deterministic chunking
    -> embedding/index adapter (future)
    -> versioned corpus publication (future)
    -> cache namespace/version change
    -> audit/provenance evidence
```

The existing PostgreSQL + Redis + Celery architecture should be exhausted before a new streaming dependency is introduced.

## Evaluation requirements

Before retrieval activation, automated evidence must cover at minimum:

- tenant leakage: zero tolerance
- restricted-data leakage: zero tolerance
- consequential autonomous decisions: zero tolerance
- citation correctness
- citation completeness
- source freshness
- source-scope correctness
- groundedness
- retrieval recall
- abstention correctness
- prompt-injection resistance
- poisoned-source resistance
- stale/superseded-source rejection
- cache isolation
- cache invalidation by corpus/policy version
- P95 latency
- cost/query once an external provider exists

Passing functional tests alone does not constitute retrieval readiness.

## Current implementation status

Implemented:
- provider-neutral intent routing contract
- evidence-source validation contract
- deterministic privacy-preserving cache-key contract
- post-retrieval Answer Authority Gate
- retrieval-source JSON schema
- focused automated tests

Not implemented / not activated:
- real ingestion
- embeddings
- vector database
- semantic retrieval
- external generation provider
- production cache of generated answers
- event-driven re-indexing
- retrieval metrics dashboard
- production RAG certification

## Infrastructure decision

Do not add Confluent or another event-streaming platform at this stage.

The architecture is intentionally modular so that a streaming platform could be introduced later if measured event volume, latency, or operational coupling demonstrates that CROWN's existing PostgreSQL/Redis/Celery stack is insufficient.
