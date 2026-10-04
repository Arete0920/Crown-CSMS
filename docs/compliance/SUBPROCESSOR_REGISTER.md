# CROWN Subprocessor Register

**Status:** Current planning register; production vendors must be verified from deployed configuration and executed agreements.

This register intentionally does not name a vendor as active merely because source code, an adapter, or a historical document mentions that vendor.

| Processing category | Purpose | Current production status | Required before activation |
|---|---|---|---|
| Application hosting / storage | Host CROWN application data, files, logs, and backups | Verify from selected deployment | Security review, data location, contract/DPA, access, backup, incident and deletion terms |
| Production database | Store tenant application records | Verify from selected deployment | Encryption, access control, backup/restore, region and retention evidence |
| Email delivery | Transactional school communications | Verify before use | Contract terms, minimum necessary data, retention, incident obligations |
| SMS delivery | Optional text notifications | Verify before use | Consent/opt-out support, contract terms, minimum necessary data, retention |
| Payment processor | Tuition/payment processing | **NOT SELECTED / PAYMENT PROCESSING DISABLED** | Processor contract, PCI responsibility matrix, tokenization/hosted-payment design, webhook/refund/settlement/reconciliation evidence |
| Identity provider | Authentication / SSO | Verify from selected deployment | Least privilege, tenant binding, audit and incident terms |
| Error monitoring / logging | Reliability and diagnostics | Verify before production use | PII minimization/redaction, retention, access and contract terms |
| Analytics / BI | Optional operational analytics | Verify before production use | Aggregation/minimization, no behavioral advertising, no unrelated profiling |
| Support / helpdesk | Customer support | Verify before production use | Confidentiality, restricted support access, retention and deletion terms |
| External generative-AI provider | Optional AI-assisted functions | **NOT AUTHORIZED / NOT SELECTED** | Privacy/security review, no training or secondary use of customer data, retention limits, processor terms, de-identification controls and approved data-flow evidence |

## Governance

Before any provider is treated as an active subprocessor, CROWN must verify and retain:

- legal vendor identity and service purpose;
- data categories and minimum necessary processing;
- processing/storage region where applicable;
- contract/DPA and security terms;
- incident-notification obligations;
- deletion/return and retention terms;
- customer notice requirements;
- current owner and review date.

Repository references alone are not evidence that a provider is active in production.
