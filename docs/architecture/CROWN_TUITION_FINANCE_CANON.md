# CROWN Tuition and Finance Canon

Status: Stage 1 Canon
Scope: Tuition Builder, Financial Aid handoff, Payment Plan preview, Billing/Ledger handoff, and Heritage Christian Academy demo setup.
Runtime impact: None.
Code impact: None.
Migration impact: None.

## Purpose

This canon locks the operating rules for the CROWN tuition and finance integration sprint before runtime code is changed.

This stage is documentation only. It exists to prevent churn, hidden assumptions, scope creep, and disruptive changes to the existing platform.

## Sprint structure

The tuition and finance work will be completed in 10 proof-gated stages:

1. Canon and guardrails
2. Tuition Builder models
3. Heritage Christian Academy seed foundation
4. Tuition quote engine
5. Admissions and parent journey integration
6. Financial Aid handoff
7. Payment plan preview and selection
8. Billing and ledger handoff
9. Mock payment provider
10. Heritage Christian Academy proof and policy scenarios

No stage may begin until the prior stage is marked PASS.

## Non-disruption rule

The existing admissions, billing, ledger, parent portal, and finance behavior must not be replaced or disrupted unless the current stage explicitly requires it.

Default implementation approach:

- Additive first.
- No opportunistic cleanup.
- No unrelated refactors.
- No broad rewrites.
- No production payment provider behavior until provider details are verified.
- No sales/demo completion claim unless configured and verified.

## Core architecture

The finance flow is:

Parent application
-> Tuition Builder
-> Financial Aid decision, if applicable
-> Net tuition
-> Payment plan preview and selection
-> Billing schedule
-> Ledger charges and payments
-> Payment provider
-> Receipts, statements, reconciliation, and reporting

## Tuition Builder responsibility

The Tuition Builder calculates the published tuition amount for the student based on:

- School
- School year
- Program
- Division
- Grade level
- Daycare or early education schedule where applicable
- Half-day or full-day schedule where applicable

The Tuition Builder produces gross published tuition before financial aid.

## Tuition policy

Published tuition is the parent-facing grade/program tuition amount.

Technology, curriculum, textbooks, standard academic resources, and routine grade-level academic costs are included in published tuition.

These may be tracked internally as tuition cost components for analysis, financial planning, board reporting, and financial aid review.

Parents should see one clean tuition amount, not a stack of routine academic fees.

## Internal tuition components

CROWN may track internal tuition components such as:

- Instruction
- Curriculum
- Textbooks
- Standard technology
- Academic resources
- Lab/resource cost
- Grade-level operating cost
- Graduation-related operating cost where applicable

Internal tuition components are not separate parent charges by default.

## Financial Aid rule

Financial Aid is the only source of tuition reduction.

Not allowed outside Financial Aid:

- Sibling tuition discount
- Staff tuition discount
- Church/member tuition discount
- Hardship tuition discount
- Bulk/family tuition discount
- Manual tuition reduction without approved aid/award record

Financial Aid is awarded before payment schedule finalization.

Payment schedules are generated only from final net tuition after approved Financial Aid, or from gross tuition when no aid applies.

## Financial Aid application fee

The Financial Aid application/admin fee is:

- One family-level fee
- Paid upfront when the family applies for Financial Aid
- Not per child
- Not rolled into tuition
- Not included in payment plans
- Not discounted by number of children

Heritage Christian Academy demo value:

- Financial Aid application fee: 40.00

## Application and re-enrollment fees

Application and re-enrollment fees are standalone upfront process fees.

They are not tuition.
They are not rolled into tuition.
They are not included in payment plans.

Heritage Christian Academy demo rule:

- First child in family cycle: 85.00
- Each additional child in the same family cycle: 50.00

This rule applies only to application and re-enrollment fees.

It does not apply to tuition.

## No enrollment deposit

CROWN will not model a separate standard enrollment deposit for this sprint.

After acceptance and Financial Aid finalization, the family selects a payment plan.

The first tuition payment is generated from the selected payment plan.

## Payment plan options

CROWN will support these tuition payment plans:

1. Annual
2. Twice-a-year
3. Monthly 10
4. Monthly 12

Plan behavior:

- Annual: 1 installment
- Twice-a-year: 2 installments
- Monthly 10: 10 installments
- Monthly 12: 12 installments

Application fees, re-enrollment fees, and Financial Aid application fees are excluded from tuition payment plans.

## Daycare and early education

Daycare and early education require schedule-based pricing.

Supported schedule dimensions:

- 2 days per week
- 3 days per week
- 5 days per week
- Half-day
- Full-day
- Daily drop-in

Daycare:

- Year-round
- 12-month billing recommended for demo
- 10-month billing allowed

Early Education:

- Academic-year default
- 10-month billing recommended for demo
- 12-month billing allowed

## Extended care

Before-care and after-care are optional extended-care charges.

They are separate from tuition.

Supported extended-care types:

- Before-care monthly
- After-care monthly
- Before plus after-care bundle
- Before-care drop-in
- After-care drop-in
- Late pickup fee

## Separate optional or usage-based charges

These are outside base tuition:

- Before-care
- After-care
- Late pickup
- Drop-in daycare
- Summer camp
- Lunch
- School store
- Sports participation
- Activities
- Field trips
- Event tickets
- Donations
- Fundraising

These should flow through the Money Spine later, but they are not part of base tuition.

## Summer camp

Summer camp is separate from academic tuition.

Summer camp is an optional billing stream.

It may support:

- Weekly sessions
- Full-session pricing
- Half-day or full-day options
- Camp before-care
- Camp after-care
- Camp registration fee
- Camp cancellation policy

## Withdrawal, refund, and proration

CROWN must support school-level policy configuration for:

- Withdrawal date
- Last day attended
- Tuition earned through date
- Future tuition cancellation
- Future Financial Aid cancellation
- Refund due
- Balance due
- Non-refundable upfront fees
- Optional charge treatment

This policy is not implemented in Stage 1. It is locked as a required later-stage item.

## Late and mid-year enrollment

CROWN must support late and mid-year enrollment policy configuration for:

- Start date
- Prorated tuition
- Remaining installments
- Catch-up first payment
- Financial Aid proration

This policy is not implemented in Stage 1. It is locked as a required later-stage item.

## Payment providers

Approved provider candidates:

1. CompUWorks
2. Metro Merchant Services of Bear, Delaware
3. Square / Block

Provider-specific production behavior must not be coded until API, hosted checkout, tokenization, webhook, ACH/card, refund, dispute, settlement, and reconciliation details are verified.

The correct Stage 9 approach is:

- Provider adapter interface
- Mock provider first
- No raw card or bank data storage
- Webhook-first finalization
- Idempotency checks

## Ledger and billing

Existing billing and ledger models must not be replaced blindly.

New work must integrate with existing structures carefully.

Expected existing concepts include:

- Billing runs
- Invoices
- Invoice lines
- Installment plans
- Installment schedule items
- Ledger accounts
- Charges
- Payments
- Allocations
- Dunning
- Chargebacks
- Payout audits

Stage 8 will inspect exact current files before integration code is written.

## Parent-facing quote structure

Parent quotes must separate:

1. Due now
2. Tuition
3. Financial Aid
4. Payment plan preview
5. Optional services

Due now may include:

- Application fee or re-enrollment fee
- Financial Aid application fee, if applicable

Tuition should show:

- Published tuition
- Financial Aid award, if approved
- Net tuition

Payment plan preview should show:

- Annual
- Twice-a-year
- Monthly 10
- Monthly 12

Optional services should be separate.

## Verification standard

Every stage must end with:

- Branch
- Commit
- Files changed
- Migrations created
- Tests run
- Test result
- Known failures
- Items not verified
- Rollback path
- Decision: PASS, FAIL, or HOLD

No next stage begins unless the current stage is PASS.

## Stage 1 completion criteria

Stage 1 is complete only when:

- This canon exists.
- Heritage Christian Academy canon exists.
- No runtime code changed.
- No migrations were created.
- Git diff shows documentation-only changes.
- Stage 1 branch is ready for review.
