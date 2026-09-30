# CrownPass Implementation Matrix v1

**Branch:** `feature/crownpass-foundation`
**Canon:** `docs/product/CROWNPASS_CANON.md`

Legend:
- **KEEP** — useful implementation can remain with hardening
- **EXTRACT** — useful implementation should move behind CrownPass ownership
- **HARDEN** — feature exists but requires stronger production behavior/evidence
- **BUILD** — missing capability
- **DEFER** — explicitly later

| Capability | Current repository evidence | Disposition | Next engineering action |
|---|---|---|---|
| Event record | `backend/advancement/models.py::Event` | EXTRACT | Map to canonical Crown Event + EventTicketingProfile; do not duplicate school event truth |
| Basic ticket | `backend/advancement/models.py::Ticket` | EXTRACT/HARDEN | Preserve IDs/migration compatibility; add lifecycle, holder, order, transfer and credential boundaries |
| QR value | Ticket `qr_code` | HARDEN | Replace raw static-string assumption with AdmissionCredential abstraction |
| QR scan audit | `TicketScan` and QR check-in service | KEEP/EXTRACT | Move behind CrownPass scan service; retain accepted/duplicate/invalid semantics |
| Check-in action | Ticket ViewSet + `qr-checkin/` | KEEP/HARDEN | Standardize check-in, check-out, validate-only modes and action permissions |
| Purchase ticket endpoint | `purchase/ticket/` | HARDEN | Replace payment-on-hold adapter with shared Crown Payments fulfillment contract |
| Payment webhook | provider webhook not configured | BUILD | Integrate approved processor through Crown Payments; idempotent fulfillment |
| Ticket frontend | `frontend/dashboards/src/modules/advancement/TicketsPage.jsx` | EXTRACT/HARDEN | Split staff box-office/admin workflows from family ticket wallet |
| Gate UI | `TicketCheckInPage.jsx` | KEEP/HARDEN | Add camera scanner, manual search, event selector, gate identity, volunteer mode, sync state |
| PDF ticket | `backend/advancement/tickets_render.py` | KEEP/HARDEN | Generate actual scannable QR/barcode image; brand with CrownPass |
| Venue | Advancement venue models/routes | EXTRACT | CrownPass venue access contract; resolve ownership with facilities/events |
| Seating map | Advancement seating models/routes | KEEP/EXTRACT | Preserve existing model behavior; add accessible seating metadata |
| Seat hold | `seat-holds`, hold endpoints | KEEP/HARDEN | Concurrency/expiry/atomicity tests; prevent oversell |
| Seat assignment | existing seating assign endpoint | KEEP/HARDEN | Add explicit audit and supervisor override policy |
| Section pricing | event section pricing endpoint | KEEP | Normalize into TicketType/price tier contract |
| Best available | best-available checkout endpoint | KEEP/HARDEN | Connect to Crown Payments and atomic ticket issuance |
| Apple Wallet | `wallet/apple/tickets/<ticket>.pkpass` | KEEP/HARDEN | Brand, sign, update, expiration/revocation and event-change support |
| Google Wallet | wallet link endpoint | KEEP/HARDEN | Implement event-ticket object lifecycle and rotating barcode option |
| Family App My Tickets | not proven end-to-end | BUILD | Add CrownPass navigation and authorized ticket/pass retrieval |
| Family App My Passes | not proven | BUILD | Reusable season/family/student/staff pass wallet |
| Guest checkout | not established as CrownPass contract | BUILD | Low-friction email/phone guest identity with secure ticket retrieval |
| Ticket transfer | no complete CrownPass flow verified | BUILD | Pending/accepted/canceled transfer state; prevent entitlement duplication |
| Season pass | no complete CrownPass flow verified | BUILD | Event eligibility + redemption windows/limits + optional renewal |
| Family pass | not verified | BUILD | Household-aware but transferable policy controlled by school |
| Student/staff pass | not verified | BUILD | Core identity-backed entitlements; privacy-minimized scanner display |
| Promo codes | not verified | BUILD | Percentage/fixed discount, dates, quantity, cart limit, scope |
| Presale/access codes | not verified | BUILD | Hidden ticket levels and early access windows |
| Complimentary tickets | not verified | BUILD | Direct issue + 100% promo path + audit reason |
| Refund workflow | not verified end-to-end | BUILD/HARDEN | Full/partial refund, ticket revocation and reporting reconciliation |
| Event cancel/postpone | not verified | BUILD | Bulk update, wallet update, attendee communication, refund policy |
| Manual lookup | not complete in CrownPass gate UI | BUILD | Search by purchaser/holder/order/email/phone/seat with restricted data |
| Offline scanning | not verified | BUILD | Downloaded scoped manifest, local append-only scan queue, reconnect conflict handling |
| Gate/device identity | not verified | BUILD | Gate and scanner device records + per-device authorization |
| Volunteer mode | not verified | BUILD | Scan/lookup only, no financial or unrelated student/family data |
| Check-out/re-entry | not verified | BUILD | Policy-driven state machine; strict online mode option |
| Dynamic/rotating QR | not present as canonical service | BUILD | TOTP-like per-ticket rotating credential; anti-replay; Google Wallet support |
| Walk-up POS | not verified | BUILD | Shared Crown Payments card-present path; cash recording optional |
| Ticket delivery | basic flows exist indirectly | HARDEN | Email/SMS delivery through Crown Communications |
| Event holder messaging | not CrownPass-specific | BUILD | Segment all ticket holders by event/ticket type and message through Communications |
| Sponsorship | existing Advancement sponsorship features | KEEP/INTEGRATE | Expose placements to CrownPass without moving donor truth into CrownPass |
| Donations at checkout | advancement capability nearby | INTEGRATE | Optional donation prompt via Advancement/Crown Payments contract |
| Order reporting | partial transaction structures | BUILD/HARDEN | Order list with channel, fees, discounts, payment and refund state |
| Attendance reporting | scan data exists | HARDEN | No-show, timestamps, gate/scanner, scan velocity |
| Finance reconciliation | event-ticket transaction category exists | HARDEN | Reconcile gross, discounts, refunds, processor fees, school net, Crown share |
| Automated finance report | not verified | BUILD | Scheduled delivery through Crown Communications |
| Accessibility | not verified | BUILD | WCAG UI, accessible seating, printable fallback, wallet accessibility content |
| Observability | not CrownPass-specific | BUILD | Payment/issuance/scan sync metrics and operational alerts |
| Certification pack | module matrix says not verified | BUILD | CrownPass-specific tenant/RBAC/runtime/load/payment/wallet/offline evidence |

## Recommended code ownership target

```
backend/crownpass/
  models/
  services/
  api/
  permissions/
  wallet/
  scanning/
  reporting/
  tests/
```

The migration must be incremental. Existing Advancement migrations and public behavior must not be broken merely to achieve folder cleanliness.

## First coding tranche

Keep the first tranche intentionally small:

1. Define CrownPass service boundary without moving database tables yet.
2. Add compatibility services around current Event/Ticket/Scan/Seating assets.
3. Introduce lifecycle enums/contracts for order, ticket, transfer and admission.
4. Create read-only Family App My Tickets API against existing ticket data.
5. Harden QR verification behind a credential service abstraction.
6. Add CrownPass permission namespace and scanner/volunteer role contract.
7. Write regression tests proving existing Advancement ticket flows remain intact.
8. Only then begin model/table extraction where the benefit justifies migration risk.

## First tranche exit criteria

- no duplicated Event or Ticket source of truth
- existing ticket purchase/check-in behavior remains regression-tested
- Family App can read authorized tickets
- scanner actions have explicit CrownPass permissions
- admission credential verification is no longer coupled directly to a raw `qr_code` string
- payment remains fail-closed until the approved processor contract is active
- no repository hygiene limits are raised

