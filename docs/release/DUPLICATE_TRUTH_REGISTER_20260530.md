# Duplicate Truth Register (2026-05-30)

Purpose: controlled register of overlapping table/model truths with explicit canonical owner and containment status.

**Option A payment ownership reconciliation:** 2026-08-12. For external money movement, this register follows the later canonical ownership map and supersedes the original OVL-005 assignment.

| overlap_id | overlap_surface | canonical_owner | duplicate_surface | status | disposition |
| --- | --- | --- | --- | --- | --- |
| OVL-001 | student identity | households.Student | core.Student | status: controlled | core.Student locked to compatibility/migration reads only |
| OVL-002 | guardian identity | households.Guardian | core.Guardian | status: controlled | core.Guardian locked to compatibility/migration reads only |
| OVL-003 | household/family identity | households.Household | core.Family | status: controlled | core.Family locked to compatibility/migration reads only |
| OVL-004 | enrollment truth | academics.Enrollment | core.Enrollment | status: controlled | core.Enrollment locked to historical compatibility only |
| OVL-005 | external payment/refund money-movement truth | payments.Payment / payments.Refund | finance.FinancePayment / finance.FinanceRefund; operational ledger payment/allocation projections; PaymentIntentRecord and GatewayEvent telemetry | status: controlled migration | Payments is canonical external money-movement authority. Finance and ledger payment/refund surfaces remain compatibility/projection paths until consumer inventory, data comparison, reconciliation, rollback, runtime proof, and independent review are complete; they must not be treated as canonical provider/payment authority. |
| OVL-006 | assignment identity | academics.Assignment | gradebook.assignment_name (legacy) | status: controlled | string shadow retained only for transitional compatibility |
