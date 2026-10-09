# CROWN Cross-Conversation Context and Decision Continuity

**Status:** Governance policy proposed for acceptance through the repository change-control process  
**Scope:** CROWN product development, implementation, release, operations, support, marketing coordination, and owner/buyer/investor preparation  
**Human authority:** Founder / Product Owner  
**Record date:** 2026-10-09

## 1. Purpose and boundary

CROWN must have one consistent, reviewable project context across separate work sessions, conversations, and contributors. Previously accepted decisions must not be silently re-litigated or replaced with stale recollections. Work must remain evidence-based.

Conversation history, generated summaries, or assistant memory are useful discovery aids **but are not authoritative source records** and cannot guarantee automatic synchronization. Source-of-truth status is conferred by the applicable approved repository or controlled private record and its change history, not by a chat response.

This policy is an authority *routing rule*. It does not replace the domain-specific policies already named in `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`.

## 2. Authority hierarchy

When instructions or artifacts differ, apply the following subject-specific hierarchy, without overriding mandatory law, security requirements, or explicit human approvals:

1. **Current authorized owner decision** for the relevant subject, supported by an identifiable acceptance or approval record. A live direction can initiate change but does not retroactively make an unmerged source change tested, deployed, or accepted.
2. **Current accepted canonical source** indexed in `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`, including the domain policy, accepted decision index, and exact current release status.
3. **Current exact-head implementation and verification evidence**, separately from deployment/runtime, provider enablement, and human approval.
4. **Controlled supporting documents**, linked to a canonical authority without contradicting it.
5. **Historical, proposed, and superseded materials**, which support provenance only.

If two apparently current records conflict, classify the item as **CONFLICT / DECISION REQUIRED**, compare dates and scope, and obtain or document the authorized resolution. Do not silently treat a proposed plan or historical note as accepted policy.

## 3. Decision state is not execution state

A material decision can be `PROPOSED`, `APPROVED`, `SUPERSEDED`, or `REJECTED`.

Implementation and evidence are tracked separately:

- `NOT STARTED` — decision recorded but no execution verified.
- `IN PROGRESS` — work begun but acceptance criteria unmet.
- `IMPLEMENTED / NOT VERIFIED` — change exists but applicable verification is absent or incomplete.
- `VERIFIED IN SOURCE` — specific exact-head checks support a code/source conclusion.
- `VERIFIED IN RUNTIME` — separate environment-specific evidence supports an operational claim.
- `BLOCKED` — concrete blocker named, evidence retained, next action specified.

A merged PR, green workflow, completed slide deck, policy approval, or marketing plan does not by itself establish production deployment, successful end-to-end behavior, contracting, or provider readiness.

## 4. Required decision capture

For any material new or changed owner decision, record at minimum:

| Field | Required content |
| --- | --- |
| Subject and scope | Product/module/business process affected |
| Decision | Precise approved rule, numeric assumption, or architectural choice |
| Status and authority | Proposed/approved/superseded/rejected; named owner or authorized approver |
| Effective date and source | Date, decision link or traceable approval context |
| Supersedes | Earlier entry, policy, pricing rule, name, or assumption displaced |
| Implementation state | Distinct from approval; with PR/commit/task reference if relevant |
| Evidence and verification | Exact SHA or dated external proof; otherwise `NOT VERIFIED` |
| Confidentiality | Public repository or access-controlled private business record |
| Review trigger | Change in product, law, contract, release, or underlying evidence |

Update the **existing canonical domain record** and its index where one exists. Do not scatter duplicate "final" versions into unrelated files. Business plans, financial projections, staffing packages, negotiated partner terms, and buyer diligence material require an appropriately controlled **private** business register or source, not a public repository commit.

## 5. Fresh-session retrieval and handoff

Before substantive work in a new session:

1. Identify the authoritative CROWN repository and resolve current source state.
2. Read the canonical index, current release status, this policy, and the domain-specific authority for the request.
3. Retrieve relevant approved **private** business/operating decisions through an authorized source if the task involves staffing, pricing, investors, marketing, contracts, or internal operations.
4. Reconcile owner directions with current canon; do not assume that every previous conversation can be retrieved in full.
5. Establish current task state: last accepted outcome, open issue/PR or deliverable, exact evidence, blockers, and next independently verifiable step.

At the end of any material work, leave a concise handoff in the governing issue, PR, document, or private decision record: `DECIDED`, `CHANGED`, `VERIFIED`, `NOT VERIFIED`, `BLOCKED`, and `NEXT ACTION`. A chat-only conclusion is insufficient for persistent cross-session continuity.

## 6. Change, verification, and closure

- Inspect existing work before proposing a replacement. Fix root causes and continue the authorized work rather than repeatedly reopening settled discussion.
- Use the repository's established branch/PR, exact-head tests, scans, review, rollback, and solo-maintainer control path. Do not merge against missing or failed required checks.
- Verify claimed interface, route, link, wizard, permissions, and runtime behavior with applicable evidence; clearly identify any untested environment.
- Do not call an issue, PR, feature, diligence item, or deployment "complete" without its own closure criteria and authority.
- Correct errors in the authoritative source rather than creating a second competing truth.
- External provider contracts, legal/compliance certifications, production credentials, physical-machine behavior, and live delivery cannot be inferred from source inspection alone.

## 7. Tool and conversation limitations

Project-level instructions and shared project sources can make new conversations more consistent, but they do not guarantee complete recall, background reading, automatic commits, or real-time context replication. The project owner must configure the conversation workspace and make its approved sources available. Each new work session must retrieve and validate current authority. When the source cannot be reached, state the missing evidence; do not invent synchronization or verification.

**Acceptance note:** This document becomes binding repository governance only after the required approved merge and the canonical index update. Until then it is a proposal under review.
