# CROWN SOC 2 Scope Decision — Draft for Management Approval

**Status:** DRAFT / NOT APPROVED  
**Prepared:** 2026-10-08  
**Purpose:** Establish the proposed initial SOC 2 readiness boundary from current repository and connected-platform evidence.

## Service organization

**Proposed service organization:** Arete Advisory Group LLC, operating the CROWN Christian School Management Solution.

This remains subject to confirmation against the legal contracting entity and auditor engagement documents.

## Initial product scope

**Include:** CROWN platform components intended for hosted school operations, including application/backend services, administrative and school portals, data stores, background processing, CI/CD, source-control governance, identity/access, logging/monitoring, backup/recovery, support access, and enabled integrations that affect customer data or service security.

**Diadem:** Do not include Diadem in the initial readiness boundary until its actual enabled service, infrastructure, data flows, contracts, and operational ownership are documented. If Diadem is enabled on the same CROWN infrastructure or shares customer data/control operation, reassess inclusion before auditor scoping.

## Hosting and deployment boundary

Repository authority currently states:

- Azure is the selected hosted destination.
- CROWN is currently **undeployed**; repository CI and deployment workflows do not establish hosted operation.
- No successor production deployment, runtime identity, or operational acceptance is asserted by `docs/CURRENT_RELEASE_STATUS.md`.
- The Azure readiness path references intended resources such as `crown-rg`, `crown-api-prod`, `crown-api-dev`, and `crownregistry`, but the repository explicitly states that actual Azure resources, subscription, region, cost, and credentials remain unverified.
- Automatic Azure drift checks are disabled and require explicit manual execution.
- A connected Render workspace check on 2026-10-08 returned no services and no PostgreSQL instances; Render is therefore not evidence of the current CROWN production environment.

**Open scope evidence:** actual Azure subscription/tenant, selected region(s), deployed services, database, broker/worker/beat services, identity, networking, storage/backups, monitoring, and exact deployed source identity.

## Payment boundary

Payment processing remains **disabled / fail closed / not authorized for activation** in the current release authority.

Planning evidence identifies Metro Payment Technologies as the intended payment-processing partner, with a tokenized hosted-gateway design and school-specific merchant accounts. Provider compliance/API documentation, gateway confirmation, contract/DPA, PCI responsibility allocation, regions, credentials, and activation approval remain outstanding.

Until those items are complete, payment processing is not an operating in-scope production integration.

## Trust Services category

**Proposed initial category:** Security.

Availability, Confidentiality, Processing Integrity, and Privacy should be evaluated with the CPA against actual customer commitments and the approved system description. Security-relevant systems cannot be excluded merely because an optional category is not selected.

## People and operating roles

Current policy drafts use the following accountable roles:

- Founder/Product Owner
- Engineering/Operations
- Privacy/Legal
- Implementation/Customer Success / School Success
- Independent reviewer / CPA where required

Actual named individuals, deputies, conflicts, after-hours coverage, and access responsibilities remain to be recorded before readiness closure.

## Subservice organizations and vendors

Treat providers as **candidate/planned** until actual activation and contract evidence exists. For each active provider, record legal entity, service, data categories, region, security assurance, contract/DPA, incident terms, retention/deletion, access model, owner, approval date, and customer-notice obligations.

No provider certification is inherited automatically by CROWN.

## Scope decisions still requiring management approval

1. confirm Arete Advisory Group LLC as the contracting/service organization;
2. approve CROWN as the initial service boundary;
3. approve Diadem inclusion/exclusion rationale;
4. confirm Azure subscription, tenant, region(s), and actual deployed resource inventory;
5. approve the in-scope Trust Services categories;
6. name actual control owners/deputies and evidence custodian;
7. confirm customer commitments and complementary user-entity controls;
8. define the readiness assessment date and evidence repository;
9. identify the independent readiness reviewer and CPA engagement path.

## Claim boundary

This document narrows the readiness scope but does not establish production operation, management approval, SOC 2 readiness completion, or independent assurance.
