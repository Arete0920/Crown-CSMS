# CROWN Subprocessor Register

**Status:** Candidate inventory / ACTIVE VENDORS AND APPROVALS UNVERIFIED  
**Reconciled:** 2026-10-23 — product direction, not vendor approval

The detailed candidate inventory is [CROWN_SUBPROCESSOR_REGISTER_20260529.csv](CROWN_SUBPROCESSOR_REGISTER_20260529.csv). Its rows are unverified service categories and planning candidates, not a customer-facing approved-vendor list.

The previous short list named hosting, payment, messaging, and monitoring vendors without activation, location, or contract evidence. Those entries must not be used as proof of current vendor selection or assurance. Reconcile each category against the selected deployment and actual agreements before publishing a customer subprocessor list.

## Required records before activation

Record actual vendor/legal entity, service, enabled environment, data categories/flow, processing/storage regions, access, security review and report scope, contract/DPA, confidentiality/purpose limits, incident terms, retention/return/deletion, owner, approval date, customer authorization/notice, and review date.

Record inactive, candidate, approved, active, and retired dispositions separately. Review before onboarding, annually, and after material changes. Offboarding includes data return/deletion and access/credential revocation proof.

No processor, messaging service, or other integration is activated by this document. Current release and payment-activation controls remain authoritative. No provider certification or report is automatically inherited by CROWN.


## Current vendor decision — October 23, 2026

**CompuWerx is the owner-designated intended payment-gateway partner**, superseding Metro's earlier planning preference. The current source-only integration remains quarantined; there is no established signed gateway agreement, verified API/webhook signing contract, approved active payment subprocessor or live-processing authorization. See [CompuWerx contract and acceptance](../vendor-coordination/compuwerx.md). Do not conflate a gateway partner with acquiring bank, legal merchant of record, ACH provider or downstream subprocessors; obtain each entity's legal role, terms and actual data flows before finalizing the vendor register.

**Disposition:** INTENDED / CONTRACTUAL AND SECURITY REVIEW OPEN / NOT ACTIVE. Keep external payment processing disabled and fail closed. Verify all actual active infrastructure, source-control and telemetry vendors separately with dated environment inventories, DPAs, regions and shared-responsibility mappings.

## Historical planning evidence — 2026-10-08

Internal meeting evidence from 2026-09-30 identified **Metro Payment Technologies** as the then-planned payment-processing partner for CROWN, with school-specific merchant accounts and a tokenized hosted-gateway approach intended to keep sensitive cardholder data out of CROWN. The meeting also left gateway selection and provider compliance/API documentation as explicit follow-up items.

**Historical disposition:** SUPERSEDED PLANNING / NEVER VERIFIED AS ACTIVE.

Before activation, retain and review the provider's legal entity details, gateway architecture, tokenization/hosted-field documentation, ACH/SEC-code handling, security assurance, PCI responsibility allocation, contract/DPA, incident terms, processing regions, retention/deletion terms, credentials/access model, and school/customer notice requirements. No live payment activation or approved-subprocessor claim is established by the meeting record alone.
