# CROWN Subprocessor Register

**Status:** Candidate inventory / ACTIVE VENDORS AND APPROVALS UNVERIFIED  
**Reconciled:** 2026-10-18 (payment-provider direction; contractual and operating evidence still unverified)

The detailed candidate inventory is [CROWN_SUBPROCESSOR_REGISTER_20260529.csv](CROWN_SUBPROCESSOR_REGISTER_20260529.csv). Its rows are unverified service categories and planning candidates, not a customer-facing approved-vendor list.

The previous short list named hosting, payment, messaging, and monitoring vendors without activation, location, or contract evidence. Those entries must not be used as proof of current vendor selection or assurance. Reconcile each category against the selected deployment and actual agreements before publishing a customer subprocessor list.

## Required records before activation

Record actual vendor/legal entity, service, enabled environment, data categories/flow, processing/storage regions, access, security review and report scope, contract/DPA, confidentiality/purpose limits, incident terms, retention/return/deletion, owner, approval date, customer authorization/notice, and review date.

Record inactive, candidate, approved, active, and retired dispositions separately. Review before onboarding, annually, and after material changes. Offboarding includes data return/deletion and access/credential revocation proof.

No processor, messaging service, or other integration is activated by this document. Current release and payment-activation controls remain authoritative. No provider certification or report is automatically inherited by CROWN.


## Current payment-provider direction — 2026-10-18

On 2026-10-12, CROWN's owner designated **CompuWerx** as the intended payment-gateway integration partner, superseding the earlier planning preference described below. This records a product decision and a vendor-coordination lead only. It does not establish a signed agreement, approved subprocessor, validated gateway contract, sandbox credentials, provider assurance, or any live transaction authority.

**Current disposition:** OWNER-DESIGNATED INTEGRATION CANDIDATE / DUE DILIGENCE AND CONTRACT UNVERIFIED / NOT ACTIVE.

Before considering provider approval or activation, obtain independently reviewable evidence of legal entity and contracting authority; payment/ACH and PCI responsibility allocation; hosted fields or tokenization and restricted card-data flows; school-specific merchant-account model; API authentication and signed webhook verification; tenant-safe payment mutations; disputes, settlements, payout reconciliation, processing locations and downstream subprocessors; incident, retention, deletion and DPA terms; test results and approved change authority. Keep all payment functionality disabled until the separate governed release and compliance acceptance criteria pass.

Implementation remains quarantined under [CompuWerx integration status](../vendor-coordination/compuwerx.md).

## Historical planning evidence — 2026-10-08

Internal meeting evidence from 2026-09-30 identifies **Metro Payment Technologies** as the planned payment-processing partner for CROWN, with school-specific merchant accounts and a tokenized hosted-gateway approach intended to keep sensitive cardholder data out of CROWN. The meeting also left gateway selection and provider compliance/API documentation as explicit follow-up items.

**Historical disposition (2026-10-08):** SELECTED_FOR_PLANNING / NOT YET APPROVED OR ACTIVE. This earlier candidate selection is **superseded** by the 2026-10-12 owner direction; it remains solely as dated provenance of prior planning.

Before activation, retain and review the provider's legal entity details, gateway architecture, tokenization/hosted-field documentation, ACH/SEC-code handling, security assurance, PCI responsibility allocation, contract/DPA, incident terms, processing regions, retention/deletion terms, credentials/access model, and school/customer notice requirements. No live payment activation or approved-subprocessor claim is established by the meeting record alone.
