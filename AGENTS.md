# CROWN contributor and assistant entry point

Scope: the `Arete0920/Crown-CSMS` repository and work connected to CROWN. This file is a **navigation and conduct contract**, not a replacement for accepted policies, architectural decisions, or release evidence.

## Read authority before acting

1. Resolve the current `main` branch and exact SHA. Do not reuse an old SHA or predecessor-repository status.
2. Read `docs/canonical/CANONICAL_DOCUMENT_INDEX.md` for the authoritative document map, and `docs/CURRENT_RELEASE_STATUS.md` for the release-claim boundary.
3. Read `docs/governance/CROSS_CONVERSATION_CONTEXT.md` for the cross-conversation decision and handoff protocol.
4. Read the governing domain source before changing that domain, including accepted architectural decisions, change management, engineering accountability, repository workflow, quality/hygiene, naming, security, privacy, and release policies.
5. When a live owner direction conflicts with a prior documented decision, identify the conflict; record a properly authorized supersession rather than silently choosing an older or newer statement.

## Stable working contract

- CROWN is a Christian school management solution operated as a product; its repository is **not** an individual school's internal HR or administrative software project merely because CROWN's operator has internal business requirements.
- The owner controls requirements, priorities, acceptance, release, and business decisions. Automated tooling and assistants supply implementation and evidence, not independent human approval.
- Treat a decision, implementation, verification, deployment, certification, and launch as **different states**. Never infer a later state from an earlier one.
- Preserve the current owner-approved direction; do not reintroduce rejected designs, names, prices, dependencies, or obsolete assumptions by default.
- Research the blocker, reproduce it, repair the root cause, validate the repair, and finish the coherent outcome where access and evidence permit. If external access or authority truly prevents completion, state the precise remaining blocker and what was verified.
- Follow `docs/governance/CHANGE_MANAGEMENT.md`: one coherent, reversible outcome per PR, exact-base/head evidence, appropriate tests, protected gates, explicit rollback, and authorized disposition.
- Keep security, authorization, tenant isolation, privacy, and fail-closed behavior intact. Never weaken a control simply to pass a test or unblock a merge.
- Use the current naming and repository-identity rules. Historical material is provenance, not current authority.
- Do not commit secrets, personal records, confidential buyer/investor terms, copied chats, or transient generated evidence to this repository.

## Carrying decisions between conversations

A conversation is not itself a reliable durable synchronization mechanism. For any material approved decision: classify it, update the appropriate *existing* canonical source or an approved private decision register, record owner and effective date, link evidence, and explicitly supersede conflicting earlier guidance. Do not introduce a duplicate, competing authority document. A new conversation should retrieve current sources before making material recommendations or claiming work is complete.

For exact procedure, status vocabulary, and separation of public repository material from confidential operating/commercial records, see `docs/governance/CROSS_CONVERSATION_CONTEXT.md`.
