# School 13-week cash source contract

Status: offline validation/calculation foundation; Compass/Discernment activation
remains NO-GO. Controls address #258. This is not a bank reconciliation, payroll
system, production forecast or financial interpretation approval.

## Authority and inspected baseline

Inspected accepted main `8661ff650c45ce085e68f269b52a6e0b2aef87ef`; refreshed
against accepted main `3edd93f0c498b3e40fff906b25b18bf00d09c97b` after #255 merged.
Accounting owns institutional truth, Billing owns school invoices/schedules,
Student Accounts owns household obligations, Payments owns canonical settlement.
Compass consumes approved aggregates through separately authorized integration.
No routes, writes, migrations, payment activation or provider resources are added.
Merged PR #255 integrates budget variance and dashboard work; it does not supply cash
forecast evidence. Its earlier #256 source must not be mistaken for forecasting.

| Input | Existing authoritative source | Sufficiency and required reconciliation |
| --- | --- | --- |
| Opening available cash | External bank reconciliation; supporting `journal.JournalEntry/JournalLine`, accounting reports | **MISSING verified complete school cash source.** Generic ASSET balances include noncash assets. Student Accounts dashboard `net_cash_total` measures transactions, not bank balance. Require reviewed bank cash, restricted cash, board designations, holds and available cash; exact cutoff and reconciliation reference. No default zero. |
| Fund restrictions | `apps.accounting.models.institutional.Fund.restriction`; journal fund codes | Classification exists; a complete cash-by-fund reconciliation is **NOT VERIFIED**. Exclude RESTRICTED and BOARD_DESIGNATED from spendable opening cash. A fund code or generic assets total alone is insufficient. |
| Tuition obligations | `billing.Invoice.ledger_charge_id` → `ledger.Charge`; `billing.InstallmentScheduleItem.invoice` | Link and schedule exist; complete per-charge outstanding allocation/credit/refund reconciliation and reviewed collection timing are **NOT VERIFIED**. Use exactly one remaining installment occurrence, referencing one owning charge and invoice. Multiple installments may share a charge; sum must not exceed its net outstanding balance. |
| Cash settlement | `payments.Payment`, `payments.Refund`, `payments.authority_services` | Settlement lifecycle and compatibility linkage exist. Pending/authorized/settling is not cash. `finance_payment_id`/`finance_refund_id` identify legacy bridge representations, not extra transactions. Settled refunds reduce actual cash once. Verified school/provider/bank complete reconciliation is **NOT VERIFIED**. |
| Payout bank evidence | `payments.ProviderPayoutBatch/Entry`, `BankStatementImport/Entry`, `PayoutBankMatch`; `payments/reconciliation_ops.py` | Individual amount/currency/date matching exists. Match status, tolerance or processed import is not a complete reconciled cash balance. Verify full coverage, account scope, fees, currency, bank clearing date and zero unexplained difference; unresolved tolerance differences need reviewed disposition. |
| Vendor obligations | `apps.accounting.PayableBill` and `services/institutional.py` | Tenant, due date, currency, total and APPROVED/POSTED/PAID/VOID states exist. Approval/posting is not a payment. Outstanding amount after externally cleared payments and partial payments is **NOT VERIFIED**; no verified partial-disbursement source was established. Use one reviewed remaining bill commitment, not expense + journal + PO as three outflows. |
| School payroll | `hr.Employee` is a tenant-scoped staff directory | **MISSING verified payroll commitments.** Directory has no salary, dated pay run, taxes or benefits. Approved dated school obligations including all payroll components are required. Arete corporate staffing, tuition percentages and inferred averages are prohibited substitutes. |
| Other commitments | Approved school-specific dated assumption record | **MISSING verified complete recurring commitment source.** Include rent, debt, utilities, taxes, benefits and other material outflows or explicitly reviewed zero coverage. Budgets alone do not establish cash dates. Avoid overlap with payroll and vendor bills. |
| Legacy finance | `crown_api.models_finance_core`, `finance.models`, `ledger.Payment/Allocation` | Never union duplicate representations into collections. `crown_api` legacy Invoice/Payment lack canonical settlement authority. Ledger allocations apply cash to charges; noncash Credits reduce obligations without creating cash. Unlinked or contradictory facts block adapters. |

## Trusted adapter boundary

`apps.accounting.cash_forecast.calculate_reviewed_cash` is an offline service,
not an API. It re-resolves the active School and uses existing persistent
`finance.view` grants scoped to that school. Board-only, teacher, cross-school,
anonymous and inactive principals fail before financial validation. Superuser
status alone is not a grant. All nested evidence must match the school/currency.

Frozen DTOs are **trusted adapter output, never untrusted HTTP payloads**.
Reference/reviewer strings are structural provenance, not proof of approval.
This slice does not implement a bank, payroll, tuition allocation or vendor
payment adapter, persist evidence, or verify document signatures/contents.
Future adapters must obtain evidence from approved access-controlled sources,
verify reviewer authority at approval time and preserve version/digest references.
The fixture-only tests demonstrate validation behavior, not actual school data.

Each `Evidence` supplies school, USD currency, immutable source/version reference,
reconciled as-of date, verification date and school financial reviewer reference.
Each input must use the same cutoff. Future integration must record the reviewer,
reviewed assumptions and interpretation approval separately from engineering CI.
Human financial review is distinct from the solo-maintainer source merge path.

## Opening and timing

The start is an explicit school-local civil date; cutoff is the previous day.
Opening cash must be reconciled **through that cutoff**. An older reconciliation
requires an independently reviewed bridge through cutoff before adapter admission.
`available = bank_cash - restricted - board_designated - holds` exactly, with
nonnegative cent amounts. Holds are disjoint from restrictions/designations and
include encumbrances/reserves in the approved opening reconciliation. A balance
requiring unsupported overdraft or restriction treatment is NOT_READY.

Evaluation is cutoff through cutoff + 7 days inclusive; source verification must
be cutoff through evaluation. Seven days is an offline maximum, not a production
freshness policy approval. No implicit current-date fallback or FX conversion.
Timezone conversion of provider timestamps belongs in the school-scoped adapter.

There are exactly 13 half-open weeks `[start + 7n, start + 7(n+1))` covering 91 days.
Past-due commitments must have a separately approved expected payment date; never
silently move them into week one. Out-of-horizon events in the submitted packet
are rejected. Adapters inventory all obligations and document which fall outside
the horizon; they must not silently omit overdue liabilities or commitments.

## Collections, settlements and commitments

A tuition commitment requires source model `billing.InstallmentScheduleItem`,
canonical installment ID and owning ledger charge ID. A separate `Receivable`
links charge to invoice and its reconciled outstanding amount **after** valid
cash allocations and noncash credits. The adapter must validate school ownership
of invoice, household, plan, charge, allocation and credit; verify charge is not
void; reconcile schedule balance; and document collection assumptions. Future
contract extensions are required for other collection methods, discounts or
unallocated aid attribution. No guessed per-charge aid distribution is allowed.

Invoice/charge totals, allocations, credits, gateway intents and settled payments
are not forecast event source models. Duplicate installment IDs, charge/invoice
representations, or scheduled totals above the net charge fail closed. Source IDs
must be the owning model's actual IDs, never newly minted shadow representations.

Historical `SettledPayment` facts are **reconciliation evidence only**, never
added to the future roll-forward. Require unique canonical and provider/manual
receipt identities; original gross and settled refund amounts; clearing cutoff;
and consistent settled/partially_refunded/refunded status. Void/reversed/failed
and unsettled payment facts cannot be admitted. Adapters must separately inventory
excluded payments and refunds, reconcile bank fees/payouts and ACH returns,
dispositions and cleared amounts, and block unresolved differences or pending
refund exposure. Fully refunded facts have zero net history, not future income.
A verified zero settlement packet still needs reviewed evidence/count/net total.

Vendor commitments use `apps.accounting.PayableBill` ID and verified remaining
amount. Only APPROVED/POSTED, still-outstanding bills may map to an `approved`
commitment; PAID/VOID/DRAFT are inadmissible. The adapter must validate related
school ownership and approval and reconcile external cleared disbursements.
Payroll/recurring require authorized dated occurrence records with unique owning
obligation identities. Recurring representations of payroll or vendor bills must
reuse the same obligation identity, so overlaps fail. Restricted/designated
commitments need a separate future fund-aware design and are rejected here.

Each of tuition/vendor/payroll/recurring requires reviewed 91-day coverage with
exact event count and Decimal total. Missing payroll is NOT_READY; explicit zero
is valid only when the school reviewer certifies complete coverage. Totals/counts
must match the submitted events. Completeness attestations must be independently
reconciled against the source inventory; this module cannot discover omitted
records from self-consistent DTOs.

## Calculation, result and acceptance

Amounts must be finite Decimal cents, strictly positive for events and bounded
below one trillion dollars per input. Floats, sub-cent amounts, missing dates,
unapproved states, stale evidence, tenant/currency mismatches, duplicates,
coverage variance and inconsistent refunds produce `NOT_READY` with reason codes
and **no weeks or partial financial totals**. Permission failures raise denial.

For each week: closing = opening + approved expected tuition - approved dated
vendor/payroll/recurring commitments; next opening equals prior closing. Source
references accompany each week's events. Negative cash is retained and flagged,
never clamped to zero. Historical settlement totals never increase opening cash.
Results carry OFFLINE_ONLY, REVIEWED_ASSUMPTIONS and COLLECTION_TIMING_UNCERTAIN.
`INPUTS_VALIDATED` means structurally admissible offline inputs, not a dependable
operational forecast, external assurance, Compass approval or product readiness.

Acceptance evidence: accounting tests include actual persistent school grants,
negative access and financial fixtures; exact-head CI/security/release checks
remain mandatory under the solo-developer approved workaround. Revert this bounded
PR to remove the foundation; no database changes or money movement occurred.

Operational blockers remain: verified bank/restriction/holds reconciliation;
canonical per-charge collection reconciliation and timing; cleared settlement and
refund/return/fee inventory; outstanding vendor disbursements; authorized school
payroll and recurring coverage; and approved adapters with financial review.
Keep #258 open until its evidence-backed acceptance is met. Production/Compass
integration requires a separately authorized, governed change and operational
financial evidence. This document does not certify those missing inputs.
