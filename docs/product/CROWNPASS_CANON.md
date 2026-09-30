# CrownPass Canon v1
**Status:** Draft implementation authority
**Product:** CrownPass
**Parent module:** Activities / Athletics / Events
**Primary role:** Integrated digital ticketing, event admission, pass management, venue access, and event revenue workflow for Crown schools
**Branch:** `feature/crownpass-foundation`
## 1. Governing definition
CrownPass is Crown's reusable ticketing and event-access subsystem for athletics, activities, fine arts, advancement, alumni, summer programs, and other school events.
CrownPass is **not** an athletics-only ticketing engine and is **not** a second payment platform.
- Crown Core owns identity, tenant/school context, permissions, payments interfaces, notifications, audit, and shared family/mobile surfaces. · Event-producing modules own their event-specific business context. · CrownPass owns ticket products, orders, admissions inventory, passes, seating, entitlement/redemption, transfer, gate scanning, and ticketing-specific reporting. · The shared Crown payment layer owns payment-provider interaction and settlement integration. · Advancement, Athletics, Fine Arts, Alumni, and other modules consume CrownPass through approved service/API contracts.
## 2. Current repository baseline
The existing Crown repository already contains substantial ticketing assets under `backend/advancement` and associated frontend surfaces. These assets are to be **salvaged and bounded**, not rebuilt blindly.
Verified repository capabilities include:
- event records with date, location, ticket price, capacity, tickets sold, and remaining capacity · ticket records with purchaser identity, unique QR code, purchase timestamp, and check-in status · ticket purchase endpoint and frontend purchase flow · QR check-in endpoint and scan audit trail with accepted / duplicate / invalid results · PDF ticket generation · venue, seating-map, seat, seat-hold, seat-assignment, and section-pricing routes/models · best-available and held-seat checkout surfaces · Apple Wallet pass endpoint · Google Wallet ticket-link endpoint · event sponsorship surfaces · internal advancement transaction category for event tickets
Known limitations:
- external payment processing is intentionally fail-closed / on hold pending approved provider integration · the existing QR approach must be reviewed for static-code fraud exposure · Family App ticket-wallet integration is not yet proven end-to-end · Athletics / Activities integration is not yet certified end-to-end · full module certification evidence remains incomplete · ticketing logic currently sits too deeply inside Advancement and must be extracted behind a reusable CrownPass boundary
## 3. Competitive design inputs
CrownPass should adopt the strongest patterns visible across leading school/event ticketing systems while avoiding unnecessary enterprise complexity.
### HomeTown Ticketing patterns to match
- digital box office for school events · mobile and printed tickets · iOS/Android scanning · reserved seating / seat maps · season passes and renewals · walk-up point-of-sale · real-time ticket sales and attendance · promo, pass, presale, and complimentary-ticket workflows · event- and ticket-level reporting · sponsor placements · rapid staff/volunteer training · family/fan support model · account-light / low-friction ticket access
### GoFan patterns to match
- school-centered event discovery and ticketing · mobile ticket wallet · reusable passes · pass-use limits and eligibility windows · ticket and pass transfer · box-office/gate workflows · sponsorship and donation integration · event/fan promotion surfaces
### Vanco Events patterns to match
- white-label school branding · custom event pages · promotion codes and tiered tickets · reserved/general seating · attendee custom fields · volunteer-restricted scanner mode · manual attendee lookup · check-in / check-out / re-entry workflows · offline scanning with deferred synchronization · per-gate / per-scanner reporting · on-site card-present payments · unified online + gate reporting · concessions/payment-adjacent extensibility
### Eventbrite patterns to match selectively
- mobile organizer workflow · fast camera-based QR scanning · manual lookup fallback · live attendance dashboard · on-site ticket sales · configurable refund policy · partial/full refund workflow · reserved-seat map UX · ticket sharing / mobile wallet support · time-slot / session-aware check-in patterns where useful
### Security patterns to adopt
For higher-risk or higher-volume events, CrownPass should support dynamic/rotating redemption credentials rather than relying exclusively on static QR values.
Google Wallet supports rotating event-ticket barcodes using time-based one-time-password mechanics. CrownPass should implement a provider-neutral rotating-token service that can support Google Wallet directly and Crown's own Family App. Static QR may remain available for lower-risk events, printed-ticket fallback, or explicitly configured school use.
## 4. Product principles
1. **School-first:** simple enough for an athletic director, office manager, or volunteer.
2. **Family-first:** tickets should be available without unnecessary account friction.
3. **One event truth:** event metadata comes from the canonical Crown event source.
4. **One payment truth:** CrownPass never implements an independent merchant stack.
5. **One admission truth:** every admission attempt creates an auditable redemption result.
6. **Mobile-first, paper-capable:** phone experience is primary; printable fallback remains possible.
7. **Offline-tolerant:** gate operations must degrade safely when connectivity fails.
8. **Fraud-aware:** higher-risk events can require rotating credentials and real-time verification.
9. **Volunteer-safe:** scanner users receive only the minimum data required to admit guests.
10. **Reusable:** Athletics, Fine Arts, Advancement, Alumni, Camp, and Activities all consume the same ticket engine.
## 5. CrownPass product surfaces
### Family / fan surfaces
- event discovery · event details · ticket selection · reserved-seat selection · general admission purchase · guest checkout · authenticated family checkout · Apple Pay / Google Pay where supported by payment provider · My Tickets · My Passes · season passes · transferred tickets · ticket transfer · Add to Apple Wallet · Add to Google Wallet · printable/downloadable ticket where policy allows · refund request · event cancellation/postponement notice · venue information · accessibility information · door/open time · parking information · bag/security policy · calendar add · event sharing
### School administrator surfaces
- create/publish ticketed event · select source event from Crown Events · ticket types · price tiers · capacity · per-order limits · sale start/end · presale windows · access/pass codes · promo codes · complimentary tickets · hidden/VIP ticket levels · reserved/general admission · venue/seat map · accessible seating · season-pass configuration · staff/student/family passes · refund policy · transfer policy · re-entry policy · donation prompt · sponsorship placement · custom checkout questions · sales dashboard · attendance dashboard · settlement/reconciliation dashboard · export/reporting · cancel/postpone event · message ticket holders
### Gate / scanner surfaces
- event selection · pre-load event data · camera scan · manual code entry · attendee lookup by name/email/phone/order · check-in · check-out · validate-only · duplicate detection · wrong-event detection · revoked/refunded-ticket detection · seat display after scan · gate/scanner identification · offline mode · real-time verification mode · device sync status · scan velocity · local pending-sync count · volunteer mode with restricted information · emergency/manual override requiring elevated permission and audit reason
### Box office / walk-up surfaces
- sell ticket at door · cash transaction recording if school permits cash · card-present payment · contactless/mobile-wallet payment · issue digital ticket · print receipt · send ticket by SMS/email · comp ticket · seat assignment · refund/void with permission · concessions integration later through shared Crown commerce services
## 6. Ticket and pass types
CrownPass must support:
- single-event ticket · general-admission ticket · reserved-seat ticket · multi-event package · tournament pass · season pass · family pass · student pass · staff/faculty pass · booster/VIP pass · complimentary ticket · access-code ticket · timed/session ticket · multi-day ticket · zero-dollar/free registration · donor/sponsor entitlement · externally issued entitlement imported through approved integration
## 7. Target domain model
The final model names may change during implementation, but the following bounded concepts are required.
### EventTicketingProfile
Links a canonical Crown event to CrownPass configuration.
Key fields:
- school_id · event_id · sales_status · capacity_policy · sale_start_at · sale_end_at · refund_policy_id · transfer_policy · reentry_policy · credential_security_mode · published_at
### TicketType
- name · description · price · quantity/capacity · min/max per order · eligibility rule · sales window · visibility · access code requirement · seat section eligibility · fee policy
### TicketOrder
- school_id · buyer identity/contact · source channel · subtotal · discounts · fees · donations · taxes if applicable · gross total · payment status · provider reference · settlement status · created_at
### Ticket
- event · ticket type · order · holder · seat assignment · lifecycle status · redemption policy · transfer status · wallet identifiers · credential version · issued_at · revoked_at
### Pass
Reusable entitlement across one or more events.
- pass type · owner/holder · eligible events or rule · total/redemption limits · date/time windows · transfer policy · renewal status
### TicketTransfer
- ticket/pass · sender · recipient · initiated_at · accepted_at · canceled_at · status
### AdmissionCredential
- ticket/pass · credential type · static token or rotating-secret reference · valid_from · valid_until · revoked · version
Secrets must never be exposed in normal API payloads.
### AdmissionScan
- school_id · event · ticket/pass · attempted credential fingerprint · device · gate · scanner user · result · mode · scanned_at · offline flag · synchronized_at · reason code
### Gate / ScannerDevice
- school · venue · gate · device identifier · authorized events · status · last sync · real-time verification requirement
### PromoAccessRule
Supports:
- presale code · passcode · promo/discount code · single-use code batch · usage limit · per-cart limit · start/end date · ticket-type scope · event scope
## 8. Redemption security modes
Each ticketed event chooses one approved mode.
### Standard
Static signed QR credential.
Use for:
- smaller school events · printed-ticket environments · low-risk free events
Requirements:
- cryptographic signature or opaque unguessable token · server-side revocation · duplicate detection · event binding · tenant binding
### Enhanced
Rotating QR credential.
Use for:
- rivalry games · tournaments · high-demand events · events where screenshot sharing is a realistic concern
Requirements:
- short-lived rotating values · per-ticket secret · clock-tolerance window · replay detection · no credential secret in frontend/browser payload · secure wallet/app issuance path
### Real-Time Strict
Rotating credential + online verification.
Use for:
- re-entry scenarios · high-value reserved seating · events with elevated fraud risk
If connectivity is lost, policy must explicitly define whether entry pauses, falls back to a downloaded allowlist, or requires supervisor override.
## 9. Offline scanning design
CrownPass must support degraded gate operation without pretending offline mode is risk-free.
Before event:
- authorized scanner downloads event ticket manifest / verification material · data is minimized to only what the scanner needs · manifest has an expiry and event scope
Offline:
- scans are validated against locally available rules · successful scans are stored locally in an append-only queue · device shows OFFLINE state prominently · cross-device duplicate prevention cannot be guaranteed while devices are disconnected · high-risk events may disable offline admission
Reconnect:
- scan queue syncs · conflicts are resolved deterministically · duplicate/replay conflicts are surfaced to supervisor · scanner/device audit records remain preserved
## 10. Payment architecture
CrownPass calls the shared Crown payment service.
Target flow:
```
TicketOrder
  -> Crown Payments
  -> approved processor (Compuwerx target)
  -> payment authorization/settlement
  -> CrownPass fulfillment
  -> school settlement + Crown revenue accounting
```
Rules:
- no ticket becomes redeemable before approved payment/fulfillment state unless it is a comp/free entitlement · webhook/provider confirmation must be idempotent · refunds reverse ticket eligibility appropriately · chargebacks flag ticket/order history · provider credentials never live in CrownPass · payment events and ticket lifecycle events are separately auditable
## 11. Wallet strategy
### Crown Family App
Primary CrownPass home:
- My Tickets · My Passes · Upcoming Events · Past Events · Transfers · Refund status
Tickets should be cached sufficiently for venue access where policy allows.
### Apple Wallet
Use Apple's event-ticket pass model and signed pass distribution.
Support:
- event time · venue/location · seat · ticket holder · barcode where compatible · real-time pass updates · event changes/cancellation updates
### Google Wallet
Use event-ticket objects.
For Enhanced security, implement rotating barcode support using a ticket-scoped secret and server-managed object issuance.
## 12. Event operations features
Required:
- event capacity · ticket-level inventory · sales cutoff · doors-open time · venue and gates · seat maps · sections/rows/seats · accessible seating · ticket holds with expiry · purchase atomicity · sold-out/waitlist-ready state · comp allocations · staff/student allocations · home/away or school/community ticket pools where configured · event cancellation · event postponement · event rescheduling · mass ticket-holder messaging
Later:
- waitlist auto-promotion · parking passes · merchandise pre-order · concessions ordering · donor upsell · hospitality/VIP packages · dynamic pricing only if explicitly approved; not a launch priority
## 13. Reporting
CrownPass reporting must distinguish orders, tickets, scans, payments, refunds, and settlements.
Minimum reports:
- event sales summary · ticket-type sales · order list · attendee/ticket list · scan/attendance list · no-show report · scan timestamp report · scan by gate · scan by scanner · scan velocity · duplicate/invalid attempts · comp ticket usage · promo/access-code usage · reserved seat assignments · refunds · gross sales · processor fees · discounts · donations · net school proceeds · Crown revenue share where applicable · settlement status
Exports:
- CSV · printable event closeout · finance reconciliation export
Scheduled finance-report delivery may be added through Crown Communications.
## 14. Roles and permissions
Example action permissions:
- `crownpass.view_events` · `crownpass.manage_events` · `crownpass.manage_ticket_types` · `crownpass.manage_seating` · `crownpass.sell_tickets` · `crownpass.issue_comp` · `crownpass.scan` · `crownpass.supervise_gate` · `crownpass.refund` · `crownpass.view_financials` · `crownpass.manage_promotions` · `crownpass.message_attendees` · `crownpass.export_reports`
Volunteer/scanner role:
- scan and lookup only · no payment totals · no full family/student profile · no unrelated events · no configuration changes
## 15. Audit requirements
Audit:
- event publication changes · ticket-type/price changes · capacity changes · comp issuance · refunds/voids · ticket transfer · ticket revocation · seat hold/assignment override · scan supervisor override · offline sync conflicts · promotion/access-code changes · settlement adjustments · event cancellation/reschedule
## 16. Notifications
CrownPass uses Crown Communications for:
- purchase receipt · ticket issued · transfer invitation · transfer accepted/canceled · event reminder · event change · weather delay · cancellation/postponement · refund processed · pass renewal reminder · gate/parking instructions
No separate CrownPass messaging stack.
## 17. Branding
Official consumer brand: **CrownPass**
Primary positioning:
**Purchase. Pass. Enter. All in Crown.**
The approved CrownPass logo should be stored under a dedicated brand asset location such as:
```
frontend/public/brands/crownpass/
  crownpass-logo-primary.png
  crownpass-logo-light.png
  crownpass-logo-dark.png
  crownpass-icon.png
  crownpass-mark.png
```
Do not duplicate brand assets throughout feature folders.
## 18. Migration from current Advancement implementation
Do not delete or rewrite existing ticketing code until behavior is inventoried and covered.
### Phase A — Inventory
Map all current:
- models · migrations · serializers · services · endpoints · frontend routes/pages · tests · wallet logic · seating logic · payment-on-hold boundaries
### Phase B — Contract
Define reusable CrownPass service/API contracts while existing Advancement endpoints remain functional.
### Phase C — Extract
Move reusable logic behind CrownPass ownership without changing external behavior unnecessarily.
Advancement becomes a consumer for:
- fundraising event tickets · alumni events · sponsorship-linked events
Athletics becomes a consumer for:
- games · tournaments · season passes
Fine Arts becomes a consumer for:
- concerts · plays · performances
### Phase D — Family integration
Add My Tickets / My Passes to Family App and wallet flows.
### Phase E — Payment integration
Connect CrownPass order fulfillment to the approved Crown payment/Compuwerx integration.
### Phase F — Gate hardening
Implement:
- scanner role · offline cache/sync · gate/device identity · scan modes · dynamic credential option · performance/load tests
## 19. Launch priority
### P0 — required before pilot
- canonical event link · ticket types · capacity · online checkout · payment fulfillment contract · QR ticket · Family App My Tickets · email/SMS ticket delivery · basic Apple/Google Wallet · scanner check-in · duplicate/invalid detection · manual attendee lookup · basic general admission · refund/void basics · transaction/audit trail · core reporting · tenant/RBAC proof · end-to-end test pack
### P1 — strong commercial launch
- reserved seating · seat maps · season passes · family/student/staff passes · ticket transfer · promo/pass/presale codes · comp ticket workflows · volunteer scanner mode · offline scanning · check-in/check-out/re-entry · attendee messaging · sponsor placement · donation prompt · box-office/walk-up sales · per-gate/scanner analytics
### P2 — differentiation
- rotating QR credentials · advanced wallet updates · tournament packages · automated pass renewal · parking passes · concessions integration · sophisticated sponsor analytics · waitlist · predictive attendance/capacity analytics
## 20. Definition of done
CrownPass is not "done" because ticket pages render.
A certified CrownPass release requires evidence that:
- tenant isolation is enforced · action-level RBAC is enforced · event ownership is canonical · checkout is idempotent · payment failures do not issue valid paid tickets · refunds/revocations invalidate admission correctly · ticket transfer cannot duplicate entitlement · seat holds cannot oversell · capacity cannot oversell · concurrent checkout is tested · scanner duplicate handling is tested · offline behavior and conflict behavior are tested · dynamic-code replay behavior is tested where enabled · wallet passes are valid and update correctly · volunteer views redact sensitive data · Family App only exposes tickets to authorized users · reports reconcile orders, tickets, payments, refunds, scans, and settlement totals · accessibility requirements are met · audit events exist for privileged changes · event cancellation/reschedule workflow is proven · production monitoring and support runbooks exist
## 21. Initial build sequence
1. Freeze current ticketing behavior and inventory Advancement implementation.
2. Establish CrownPass service boundary and ownership map.
3. Create canonical EventTicketingProfile and TicketType contracts.
4. Normalize order/ticket/pass lifecycle.
5. Connect to Crown Payments contract.
6. Wire Family App My Tickets/My Passes.
7. Preserve and harden existing seating/QR/wallet capabilities.
8. Build scanner role, gate/device model, and offline sync.
9. Add passes, transfer, promo/comp workflows.
10. Add dynamic credential security.
11. Complete reporting/reconciliation.
12. Produce CrownPass certification evidence packet.
## 22. Explicit non-goals for first pilot
Do not delay pilot for:
- dynamic pricing · resale marketplace · third-party broker integrations · complex ticket-exchange marketplace · stadium-scale NFC hardware rollout · sophisticated concessions system · enterprise entertainment-industry promoter tooling
CrownPass should first be the best integrated ticketing experience a small-to-mid-sized Christian school needs.

