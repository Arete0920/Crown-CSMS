# Buyer Operational Transfer Register

**Status:** Preparation control; buyer operational turnover is not approved.  
**Effective date:** 2026-07-31  
**Last reviewed:** 2026-07-31  
**Repository baseline reviewed:** `d725386a6cfbb48f9967e65e15cd92db27cdfde2`  
**Controlling issues:** #1631 and #1632 under #1619

## Freshness boundary

Before this register is used or changed, verify its effective date, repository baseline, current ownership facts, active external accounts, executed agreements, controlling issues, and whether a later canonical handoff record supersedes it. Historical owner, vendor, access, billing, or contract records must not be treated as current without revalidation.

## Purpose

Repository ownership does not by itself transfer the systems, authority, agreements, credentials, evidence, or operational capability required to operate CROWN. This register defines the assets and acceptance evidence required for a controlled new-owner handoff.

## Transfer domains

| Domain | Required transfer evidence | Acceptance condition |
|---|---|---|
| GitHub | Repository ownership/admin roles, branch protection, required checks, environments, Actions ownership, release/tag authority, security alerts, and audit access | Buyer administrator independently verifies access and governance without weakening controls |
| Cloud platform | Subscription/tenant ownership, resource inventory, billing, resource groups, applications, databases, storage, backups, networking, managed identities, policy, and audit logs | Buyer can inventory, operate, monitor, deploy, and recover the approved environment |
| Microsoft 365 / Entra | Tenant ownership, app registrations, permissions, certificates, enterprise applications, consent, integration ownership, and sign-in logs | Buyer verifies identity ownership, least privilege, expiry, and operational continuity |
| Domains and certificates | Registrars, DNS zones, records, renewal authority, TLS certificates, validation methods, and expiry alerts | Buyer controls renewal and can verify active production endpoints |
| Databases and backups | Server/database ownership, backup policy, retention, restore authority, encryption, network controls, and isolated restore evidence | Buyer can identify a backup, restore it safely, validate it, and meet accepted RTO/RPO |
| Monitoring and incident operations | Monitoring resources, alert rules, destinations, log retention, dashboards, on-call ownership, escalation, and incident records | Buyer receives and validates test alerts and can execute the incident process |
| Vendors and integrations | Vendor accounts, contracts, support contacts, processing purpose, regions, data categories, billing, renewal, and termination procedures | Buyer accepts continuing obligations or records replacement/termination plan |
| Privacy and contracts | Customer agreements, DPAs, privacy notices, subprocessors, retention commitments, incident obligations, legal holds, and jurisdiction-specific duties | Buyer and qualified counsel record accepted obligations and unresolved conditions |
| Intellectual property | Source ownership, assignments, contributor evidence, trademarks, domains, documentation, designs, licenses, and third-party notices | Buyer counsel confirms the transfer package and identified exclusions |
| Support and operations | Runbooks, operators, support channels, service levels, escalation paths, known limitations, maintenance windows, and post-transfer assistance | Buyer demonstrates independent operation or signs an explicit transition-services arrangement |
| Emergency authority | Break-glass control, recovery contacts, decision authority, audit, expiry, and post-use review | Buyer performs a controlled exercise and removes seller emergency access when accepted |
| Release evidence | Approved exact SHA, artifacts, SBOM, CI, deployment identity, runtime proof, recovery proof, security proof, privacy/legal disposition, limitations, and authorization record | Buyer verifies all evidence resolves to the same unchanged release identity |

## Per-asset record

Each transferred asset must record:

- asset identifier and environment;
- current legal/business owner;
- current technical custodian;
- target owner and custodian;
- access method without recording secret values;
- dependencies and downstream consumers;
- billing and renewal owner;
- support and escalation contacts;
- applicable agreement or license;
- data categories and regions;
- backup/recovery dependency;
- transfer action and date;
- seller-access removal date;
- buyer verification method and result;
- exception, residual risk, and acceptance authority.

## Handoff sequence

1. Freeze authorized repository-changing work and select the immutable release candidate.
2. Complete Lanes 1–7 on that exact SHA.
3. Produce the final evidence index and limitations register.
4. Inventory external assets and reconcile them to repository and runtime dependencies.
5. Establish buyer-controlled accounts and least-privilege access.
6. Transfer ownership, billing, contracts, monitoring destinations, and recovery authority.
7. Have the buyer independently validate build, deployment, runtime, monitoring, backup restore, rollback, identity, and support procedures.
8. Revoke seller access not covered by a signed transition-services arrangement.
9. Record production authorization separately from buyer operational acceptance.
10. Retain signed acceptance, exceptions, residual risks, and post-transfer obligations.

## Buyer acceptance tests

The buyer must independently demonstrate or explicitly accept evidence for:

- fresh clone and reproducible build;
- dependency installation and required CI;
- exact-SHA artifact and deployment identity;
- administrator and required persona access;
- cross-tenant and privilege-escalation denial;
- monitoring alert receipt and incident escalation;
- isolated database restore and reconciliation;
- application rollback;
- operational access rotation/revocation and emergency access controls;
- privacy, contract, vendor, retention, and incident obligations;
- known limitations and deferred capabilities;
- support ownership and post-transfer change control.

## Blocking conditions

Buyer turnover remains prohibited if any material asset has unknown ownership; seller-only access; unverified billing or renewal authority; missing executed agreement; missing backup/restore capability; unresolved critical privacy or security contradiction; runtime identity mismatch; incomplete runbook; unaccepted residual risk; or evidence tied to a different SHA.

## Decision boundary

Production authorization and buyer turnover are separate decisions. Production GO does not automatically authorize operational transfer, and repository transfer does not establish production readiness. Buyer operational turnover requires a dated acceptance record identifying the accepted SHA, environment, evidence index, transferred assets, exceptions, residual risks, accountable seller authority, and accountable buyer authority.
