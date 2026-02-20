# Phase 3 Demo Proof Pack — Checklist (Operator)

This checklist exists to keep the demo surface deterministic and prevent regressions.

## A) Static Proof Gate (CI)

CI must pass the **Phase 3 Demo Proof Pack** gate (`tools/verify_phase3_demo_proof.ps1`).

Gate asserts:
- Backend ledger endpoints exist (create/record/allocate/invariants + void endpoints + open charges/invoices)
- Frontend demo pages exist on disk (Billing, Finance, Admissions, Financial Aid)
- Router imports and routes those pages

## B) Phase 3 "Demo Surface" Minimum Set

### Backend
| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/ledger/charges/` | POST | Create a charge |
| `/api/v1/ledger/payments/` | POST | Record a payment |
| `/api/v1/ledger/payments/<id>/allocate/` | POST | Apply payment to a charge |
| `/api/v1/ledger/charges/<id>/void/` | POST | Void a charge |
| `/api/v1/ledger/payments/<id>/void/` | POST | Void a payment |
| `/api/v1/ledger/charges/open/` | GET | List open charges |
| `/api/v1/ledger/invoices/open/` | GET | List open invoices |
| `/api/v1/ledger/invariants/` | GET | Ledger health verification |

### Frontend
| Component | Route | File |
|---|---|---|
| BillingDashboard | `/billing` | `frontend/dashboards/src/pages/BillingDashboard.jsx` |
| FinanceInvoicesList | `/finance/invoices` | `frontend/dashboards/src/pages/FinanceInvoicesList.jsx` |
| AdmissionsPipelineList | `/admissions` | `frontend/dashboards/src/pages/AdmissionsPipelineList.jsx` |
| FinancialAidDashboard | `/financial-aid` | `frontend/dashboards/src/pages/FinancialAidDashboard.jsx` |

## C) Manual sanity (fast, pre-demo)

1. Load each dashboard — confirm no blank screen / 500
2. Confirm all API calls include:
   - `Authorization: Bearer <token>`
   - `X-School-Id: <uuid>`
3. Confirm `/api/v1/ledger/invariants/` returns OK (or expected protected response)
4. Confirm billing dashboard shows charges and payments

## D) Phase tags (baseline discipline)

| Tag | SHA | Notes |
|---|---|---|
| `phase3-demo-proof-pack-2026-02-20` | (after merge) | Static gate baseline |

When Phase 3 P1 merges, immediately tag with `phase3-demo-proof-pack-YYYY-MM-DD`.

## E) Gate command

Run locally before any demo:

```powershell
pwsh -ExecutionPolicy Bypass -File tools/verify_phase3_demo_proof.ps1 -Mode static
```

For strict route-path checks:

```powershell
pwsh -ExecutionPolicy Bypass -File tools/verify_phase3_demo_proof.ps1 -Mode strict
```
