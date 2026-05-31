# Duplicate Truth Register (2026-05-30)

Purpose: controlled register of overlapping table/model truths with explicit canonical owner and containment status.

| overlap_id | overlap_surface | canonical_owner | duplicate_surface | status | disposition |
| --- | --- | --- | --- | --- | --- |
| OVL-001 | student identity | households.Student | core.Student | status: controlled | core.Student locked to compatibility/migration reads only |
| OVL-002 | guardian identity | households.Guardian | core.Guardian | status: controlled | core.Guardian locked to compatibility/migration reads only |
| OVL-003 | household/family identity | households.Household | core.Family | status: controlled | core.Family locked to compatibility/migration reads only |
| OVL-004 | enrollment truth | academics.Enrollment | core.Enrollment | status: controlled | core.Enrollment locked to historical compatibility only |
| OVL-005 | payment truth | finance.FinancePayment | payments.PaymentIntentRecord | status: controlled | payments app remains processor telemetry, not accounting truth |
| OVL-006 | assignment identity | academics.Assignment | gradebook.assignment_name (legacy) | status: controlled | string shadow retained only for transitional compatibility |
