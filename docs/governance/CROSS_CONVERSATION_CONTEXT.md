# CROWN Cross-Conversation Context and Decision Authority

**Status:** Canonical governance upon governed merge into `main`
**Owner decision:** Scope approved 2026-10-09; implementation completion authorized 2026-10-10
**Owner:** CROWN product owner / Arete Advisory Group
**Scope:** Product development, engineering, implementation, support, internal operations, staffing, finance, partnerships, marketing, and investor/buyer materials.

## Objective

Ensure that all work sessions apply the same approved CROWN facts, operating principles, policies, procedures, and evidence standards. Do not mistake a new conversation for a new project or automatically revive superseded decisions.

## Authority and precedence

1. Applicable law, contractual obligations, security/privacy requirements, and explicit current owner authorization govern their respective domains.
2. Current accepted repository canonical documents and indexed ADRs govern engineering, release, security, and technical change.
3. An expressly owner-approved, dated commercial or operational decision in the controlled decision register governs its domain until superseded. Confidential business records live in access-controlled storage, not this public repository.
4. Current source code, exact-head CI evidence, deployment/runtime observations, and provider confirmations establish implementation and operational *facts*. A plan or decision is not evidence that an action happened.
5. Supporting documents and dated meeting notes inform interpretation. Prior chats and model memory are pointers for retrieval, not binding records.

Owner authorization does not bypass applicable law, contractual obligations, security/privacy controls, required checks, or the governed change-control path. Business intent and implementation evidence remain separate; CI and tooling are not independent human approval.

Where authority conflicts, do not conceal the conflict. Note source, status, effective date and what approval is required to resolve it. An earlier business decision is not displaced by a newer speculative draft.

## Persistent operating principles

- **One CROWN:** The authoritative repository is `Arete0920/Crown-CSMS`; predecessor repository material is historical.
- **Solve and verify:** Investigate the failure, repair root cause, test, document evidence, and close when justified. Do not treat retries, announcements, or green unrelated checks as proof.
- **Do not weaken gates:** Maintain security, tenant isolation, least privilege, privacy, CI/release authority, and independently reversible changes.
- **Evidence over assertion:** Differentiate designed, implemented, tested, merged, deployed, externally configured, and independently assured. Use `NOT VERIFIED` for missing evidence.
- **Keep work coherent:** Prefer one PR per independently reversible outcome, honor current PR hygiene requirements, and follow the approved solo-maintainer control path.
- **Preserve decisions:** Do not reopen approved choices or silently change pricing, go-live, ownership, product boundaries, or staffing assumptions.
- **Honor scope:** Internal Arete HR/finance operations are not automatically CROWN school product features; distinguish internal tools from school-facing modules.
- **Protect data:** No credentials, student/family/personnel PII, confidential investor terms, or copied conversations in public documentation; follow existing security policy.

## Cross-chat start-of-work protocol

1. Identify the CROWN domain and requested outcome.
2. Retrieve current relevant canonical records, exact source identity, and where material the current evidence/status.
3. Retrieve the latest approved domain-specific business decision from its controlled location; if unavailable, report the gap rather than inventing continuity.
4. Work within accepted decisions; challenge only on new evidence, explicit user direction, legality/security, or a genuine contradiction.
5. Record material approved changes via the change-control or decision record with owner, approval status, effective date, prior decision superseded, scope, dependencies, and verification.
6. Update affected canonical references, investor materials, operating plans, tests, and implementation evidence in the same bounded change or a linked, tracked follow-up.
7. Finish with completed actions, verified facts, and exact unresolved blockers, not blanket completion claims.

## Business decision register pattern

Maintain a controlled register outside this public repository when commercially confidential. Each record should have:
- Decision ID, domain, exact statement, version/effective date
- Owner/approver, approval evidence, current status (PROPOSED/APPROVED/SUPERSEDED)
- Supersedes/superseded-by references
- Systems, documents, forecasts and collateral affected
- Implementation/verification state, evidence links, next review trigger

A public index may point to an access-controlled register without copying private terms.

## Scope and limits

This governance standard guides people and repository-aware assistants. It cannot force ChatGPT to automatically read other chats, synchronize memory instantly, or execute a repository check in every new thread. For highest consistency, keep CROWN work in one dedicated ChatGPT Project with stable project instructions, attach or reference the controlled decision index, and require tools to re-check current canonical documents when making consequential claims.

## Existing controlling references

- `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`
- `docs/architecture/DECISION_INDEX.md`
- `docs/CURRENT_RELEASE_STATUS.md`
- `docs/governance/CHANGE_MANAGEMENT.md`
- `docs/engineering/ENGINEERING_ACCOUNTABILITY_POLICY.md`
- `docs/engineering/REPOSITORY_WORKFLOW.md`
- `docs/governance/CROWN_PR_HYGIENE_GATE.md`
- `docs/governance/CROWN_SOLO_DEVELOPER_APPROVED_WORKAROUND.md`
- `docs/governance/SOLO_MAINTAINER_BRANCH_PROTECTION_POLICY.md`

This policy supplements, and does not replace, those authorities.
