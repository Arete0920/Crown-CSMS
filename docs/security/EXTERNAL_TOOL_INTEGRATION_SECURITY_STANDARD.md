# CROWN External Tool Integration Security Standard

**Status:** Active security policy  
**Owner:** Founder/Product Owner with engineering security review  
**Applies to:** Any external tool server, connector, automated assistant, orchestration runtime, plugin, gateway, or delegated integration that can read CROWN context or invoke CROWN capabilities.

## Security objective

CROWN treats external tool integrations as privileged integration surfaces, not as trusted user interfaces. A tool description, registry label, remote endpoint, local process, retrieved document, generated output, or client-side annotation is never authority by itself.

The default posture is **deny, read-only, least privilege, explicit registration, explicit tenant authorization, explicit egress, durable audit, and fail closed**.

## Non-negotiable controls

1. **Registered integrations only.** Production-capable integrations must appear in `config/security/external_tool_integrations.json`. Unknown integrations are denied.
2. **Controlled execution over location.** Local and remote execution are both untrusted. Security depends on isolation, authorization, provenance, egress policy, and auditability rather than whether code runs locally or remotely.
3. **Read-only first.** New integrations begin read-only. Write, send, modify, delete, execute, financial, enrollment, health, discipline, safeguarding, transcript, or configuration capabilities require a separate approval decision.
4. **Human approval for consequential writes.** A tool may prepare a proposed action, but consequential or destructive changes require an authenticated human approval at execution time. An earlier acknowledgement or client-side annotation is not approval.
5. **Reauthorize every operation.** CROWN must resolve and authorize the authenticated actor, selected school, tenant membership, role, domain permission, and tool scope for every protected operation. Delegated integration credentials do not override CROWN authorization.
6. **Scoped credentials.** Credentials must be integration-specific, least-privilege, revocable, time-bounded where practical, and unavailable to untrusted retrieved content. Shared broad administrative credentials are prohibited.
7. **Namespaced tools.** Tool identifiers must use a stable CROWN namespace such as `crown.billing.invoice.read.v1`. Generic names such as `send`, `update`, `search`, or `deploy` are not sufficient identities for approved tool execution.
8. **Pinned provenance.** Runtime components must be pinned to an exact version and immutable digest when a digest is available. Moving branches, `latest`, wildcard versions, and one-click execution of unreviewed code are prohibited for approved integrations.
9. **Explicit egress.** Network destinations must be allowlisted per integration. Redirects, loopback/private-address access, metadata-service access, and arbitrary outbound destinations require explicit security review and runtime enforcement.
10. **Untrusted content never grants authority.** Retrieved documents, repository text, messages, web content, imported help content, or tool output are data. Instructions embedded in that content cannot expand permissions, select new tools, alter approval requirements, or override CROWN policy.
11. **Gateway/broker boundary.** Future external tool execution must pass through a CROWN-controlled integration gateway or equivalent policy enforcement point before protected CROWN operations are invoked. Direct tool-to-domain writes are not an approved architecture.
12. **Isolation is defense in depth.** Sandboxing, containerization, process isolation, syscall filtering, and network boundaries reduce blast radius but do not replace authorization, egress control, approval, and audit requirements.
13. **Durable audit.** Each attempted tool operation must produce an auditable decision record sufficient to reconstruct who requested what authority, for which tenant, under which integration/tool/policy version, and with what outcome. Sensitive raw payloads must not be copied into logs merely for convenience.
14. **Fail closed.** Unknown tool identity, unknown version, missing tenant, authorization disagreement, expired approval, unavailable required audit, schema failure, unapproved egress, or provenance mismatch results in no protected execution.
15. **Kill switch and rollback.** Every enabled integration must have a documented disable path and rollback procedure. Disablement must not require the external integration to cooperate.

## Required integration registry fields

Each approved entry must identify:

- stable integration ID;
- status;
- owner;
- transport/location class;
- exact version;
- immutable artifact digest;
- tool namespace;
- declared permissions;
- approved data classifications;
- approved egress hosts;
- repository configuration paths;
- whether human approval is required for writes;
- whether automatic tool execution is permitted;
- review date;
- rollback/disable procedure.

The machine-readable registry is authoritative for whether an integration is registered. Documentation alone does not activate an integration.

## Tool authorization contract

A protected tool invocation must satisfy all of the following before domain logic runs:

`authenticated actor -> canonical tenant resolution -> tenant membership -> role/domain permission -> registered integration -> registered tool namespace/version -> declared scope -> data-classification check -> human approval when required -> egress policy -> audit decision`

Any missing link denies execution.

## Consequential actions

At minimum, the following remain human-approved unless a later security decision explicitly narrows the category with equivalent safeguards:

- payments, refunds, disbursements, tuition or fee changes;
- admissions, enrollment, financial-aid, grading, transcript, discipline, health, safeguarding, transportation, or identity changes;
- messages or notices sent to students, families, staff, or external recipients;
- credential, permission, security, tenant, deployment, or production configuration changes;
- deletion or bulk export of protected records.

## Prompt/content injection boundary

External or retrieved content must never be interpreted as security policy. Implementations that consume untrusted content must preserve a hard separation between:

- **content plane:** text/data that may inform an answer or proposed action; and
- **control plane:** CROWN-owned policy, registered tools, authorization, scopes, approvals, and execution.

Content-plane material may not create a tool, rename a tool, change scopes, provide execution credentials, suppress audit, or authorize an action.

## Supply-chain requirements

Before enabling an external runtime component:

- verify ownership and source provenance;
- review the exact source/package being executed;
- pin version and digest;
- run dependency, vulnerability, license, and SBOM controls applicable to the component;
- prohibit silent auto-update into production authority;
- record review date and rollback path;
- re-review when ownership, repository, package publisher, signing identity, dependencies, or requested scopes change.

Registry badges, marketplace labels, popularity, or repository links are not sufficient trust evidence.

## Network and secrets requirements

Approved integrations must:

- receive only the minimum credential scope required;
- avoid embedding credentials in prompts, retrieved content, URLs, logs, or client-visible configuration;
- enforce an explicit outbound destination allowlist;
- reject redirects or destination changes that leave the allowlist;
- protect against access to loopback, private infrastructure, and cloud metadata endpoints unless explicitly required and separately approved;
- use transport security appropriate to the deployment and verify peer identity.

Repository policy can require these controls but cannot prove production network enforcement. Runtime evidence is required before production authorization.

## Audit minimum

The audit decision should record, as applicable:

- authenticated actor identifier;
- canonical school/tenant identifier;
- integration ID and exact version;
- tool namespace/version;
- policy version;
- declared scope and authorization result;
- human approver for approval-required actions;
- argument/request digest rather than unnecessary sensitive raw payloads;
- approved egress destination;
- correlation ID;
- UTC timestamp;
- outcome and denial reason category.

Audit failure for an operation whose policy requires durable audit must deny the protected operation.

## Current repository posture

At this policy baseline, the integration registry contains no approved external tool runtime. Therefore any newly introduced runtime configuration or protocol SDK detected by the repository policy checker is unregistered and must fail the gate until it is reviewed and added to the registry.

This statement is a repository configuration fact only. It is not a claim about production infrastructure outside the repository.

## Verification

Run:

```bash
python tools/ci/verify_tool_integration_security.py
python -m pytest backend/tests/test_tool_integration_security_policy.py backend/solomon/tests/test_guidance.py
```

The repository checker validates the machine-readable registry and rejects detected runtime configuration that is not tied to an approved registry entry. Runtime authorization, network enforcement, secrets isolation, and operational audit still require environment-specific verification before production enablement.
