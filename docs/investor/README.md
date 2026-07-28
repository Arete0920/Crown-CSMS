# CROWN Technical Diligence Overview

## Purpose

This is the controlled starting point for an authorized technical review of the CROWN repository. It is limited to product architecture, source organization, engineering controls, security boundaries, operational requirements, known risks, and ownership-transfer verification.

Commercial outreach, buyer targeting, valuation, negotiation strategy, investor presentations, market-capture plans, and transaction structuring are intentionally excluded from this repository review path.

## Current authority

The authoritative repository is `tcmegahan/Crown2026`. The public-facing product name is CROWN.

Review these records first:

1. `README.md`
2. `docs/CURRENT_RELEASE_STATUS.md`
3. `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`
4. `docs/canonical/REPOSITORY_MANIFEST.md`
5. `docs/engineering/DEV_SETUP.md`
6. `SECURITY.md`
7. `docs/operations/README.md`

Historical reports, generated evidence, archived status documents, issue checklists, and prior marketing or investor materials do not override current canonical records.

## Product and technical scope

CROWN is a multi-tenant Christian School Management Solution with backend and frontend implementation across admissions, enrollment, academics, attendance, student records, gradebook, billing, accounting, financial aid, communications, portals, governance, transportation, athletics, safety, spiritual life, and related school operations.

The current technical stack includes:

- Django and Django REST Framework;
- React and Vite;
- PostgreSQL-oriented production data architecture;
- application authentication and Microsoft Entra-related integration support;
- Azure-oriented deployment materials and GitHub Actions automation;
- backend, frontend, contract, browser, security, dependency, and release checks.

The existence of source code, tests, workflows, or prior deployment records does not establish current production authorization.

## Current posture

CROWN is under an owner-directed repository freeze.

- Production: **NOT APPROVED / NO-GO / HOLD**
- Buyer operational turnover: **NOT APPROVED**
- External payment processing: **DISABLED / FAIL CLOSED**
- Historical-key retirement and all-ref history remediation: **NOT VERIFIED COMPLETE**

The controlling release posture is `docs/CURRENT_RELEASE_STATUS.md`.

## Technical diligence sequence

An authorized reviewer should:

1. verify repository ownership, access, branch controls, required checks, and administrator authority;
2. perform a clean clone and follow the canonical developer setup;
3. install dependencies from controlled requirement and lock files;
4. run backend, frontend, contract, browser, dependency, and security checks at one exact commit;
5. inspect architecture, authentication, authorization, tenant isolation, data models, API transport, background work, deployment topology, and operational controls;
6. trace representative critical workflows from browser route through API, authorization, tenant context, domain logic, database writes, audit events, and rendered response;
7. review dependency licenses, vulnerability results, secret-scanning results, and software-supply-chain controls;
8. inspect migration history, schema ownership, retention behavior, backup, restore, and rollback procedures;
9. verify cloud resources, domains, certificates, secrets, monitoring, logging, incident response, and external integrations;
10. confirm that a successor can clone, configure, test, deploy, operate, recover, and administer the platform without undocumented assumptions.

## Claim boundary

Appropriate statements are limited to facts supported by current source and evidence. CROWN must not be described as production authorized, buyer ready, fully tenant-certified, fully recovery-certified, universally compliant, or independently approved without current evidence supporting those claims.

## Repository boundary

This repository is an engineering and technical-diligence asset. Internal commercial strategy, prospect targeting, outreach scripts, valuation work, investor pitch material, negotiation positions, and transaction structures must be maintained outside the normal repository tree in a separately controlled transaction workspace.
