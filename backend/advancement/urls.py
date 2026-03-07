from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api import (
    DonorViewSet,
    CampaignViewSet,
    SponsorshipPackageViewSet,
    EventViewSet,
    TicketViewSet,
    StoreItemViewSet,
    GiftViewSet,
    PledgeViewSet,
    SponsorshipAgreementViewSet,
    advancement_metrics,
    advancement_summary,
    purchase_ticket,
    purchase_store_item,
    # Stage 2 functional views
    gift_checkout,
    gift_mark_paid,
    pledge_create,
    pledge_cancel,
    sponsorship_checkout,
    sponsorship_mark_paid,
    qr_checkin,
    # Stage 3 ViewSets
    RelationshipViewSet,
    ProspectViewSet,
    MoveViewSet,
    AlumniCohortViewSet,
    AlumniCohortMemberViewSet,
    MembershipTierViewSet,
    MembershipViewSet,
    VenueViewSet,
    SeatingMapViewSet,
    EventSeatingViewSet,
    SeatViewSet,
    SeatHoldViewSet,
    SponsorshipDeliverableViewSet,
    SponsorImpressionViewSet,
    # Stage 3 action views
    moves_transition,
    seating_set_layout,
    seating_hold,
    seating_assign,
    sponsorship_log_impressions,
    # Stage 3.1 – live availability + strict holds + purchase
    seating_availability,
    seating_hold_strict,
    seating_purchase_held,
    # Stage 3.2 – Stripe checkout + order status
    seating_checkout,
    order_status,
    stripe_webhook,
    # Stage 3.3 – section pricing + best-available
    seating_best_available_checkout,
    event_section_prices,
    # Stage 3.4 – sponsors, receipts, Wallet passes
    event_sponsors,
    apple_wallet_pass,
    google_wallet_link,
)

router = DefaultRouter()
router.register(r"donors", DonorViewSet, basename="advancement-donors")
router.register(r"campaigns", CampaignViewSet, basename="advancement-campaigns")
router.register(r"sponsorships", SponsorshipPackageViewSet, basename="advancement-sponsorships")
router.register(r"events", EventViewSet, basename="advancement-events")
router.register(r"tickets", TicketViewSet, basename="advancement-tickets")
router.register(r"store", StoreItemViewSet, basename="advancement-store")
# Stage 2 read-only ViewSets
router.register(r"gifts", GiftViewSet, basename="advancement-gifts")
router.register(r"pledges-list", PledgeViewSet, basename="advancement-pledges-list")
router.register(r"agreements", SponsorshipAgreementViewSet, basename="advancement-agreements")
# Stage 3 ViewSets
router.register(r"relationships", RelationshipViewSet, basename="advancement-relationships")
router.register(r"prospects", ProspectViewSet, basename="advancement-prospects")
router.register(r"moves", MoveViewSet, basename="advancement-moves")
router.register(r"alumni-cohorts", AlumniCohortViewSet, basename="advancement-alumni-cohorts")
router.register(r"alumni-members", AlumniCohortMemberViewSet, basename="advancement-alumni-members")
router.register(r"membership-tiers", MembershipTierViewSet, basename="advancement-membership-tiers")
router.register(r"memberships", MembershipViewSet, basename="advancement-memberships")
router.register(r"venues", VenueViewSet, basename="advancement-venues")
router.register(r"seating-maps", SeatingMapViewSet, basename="advancement-seating-maps")
router.register(r"event-seating", EventSeatingViewSet, basename="advancement-event-seating")
router.register(r"seats", SeatViewSet, basename="advancement-seats")
router.register(r"seat-holds", SeatHoldViewSet, basename="advancement-seat-holds")
router.register(r"deliverables", SponsorshipDeliverableViewSet, basename="advancement-deliverables")
router.register(r"impressions", SponsorImpressionViewSet, basename="advancement-impressions")

urlpatterns = [
    # KPI summary (dashboard feed)
    path("summary/", advancement_summary, name="advancement-summary"),
    # Legacy metrics (keep for backward compat)
    path("metrics/", advancement_metrics, name="advancement-metrics"),
    # Purchase endpoints (Stage 1)
    path("purchase/ticket/", purchase_ticket, name="advancement-purchase-ticket"),
    path("purchase/store/", purchase_store_item, name="advancement-purchase-store"),
    # Stage 2: Gift checkout + payment confirmation
    path("gift/checkout/", gift_checkout, name="advancement-gift-checkout"),
    path("gift/<uuid:gift_id>/mark-paid/", gift_mark_paid, name="advancement-gift-mark-paid"),
    # Stage 2: Pledge create + cancel
    path("pledges/create/", pledge_create, name="advancement-pledge-create"),
    path("pledges/<uuid:pledge_id>/cancel/", pledge_cancel, name="advancement-pledge-cancel"),
    # Stage 2: Sponsorship checkout + payment confirmation
    path("sponsorship/checkout/", sponsorship_checkout, name="advancement-sponsorship-checkout"),
    path("sponsorship/<uuid:agreement_id>/mark-paid/", sponsorship_mark_paid, name="advancement-sponsorship-mark-paid"),
    # Stage 2: QR check-in (body-based, returns scan audit record)
    path("qr-checkin/", qr_checkin, name="advancement-qr-checkin"),
    # Stage 3: Moves pipeline
    path("moves/transition/", moves_transition, name="advancement-moves-transition"),
    # Stage 3: Seating management
    path("seating/set-layout/", seating_set_layout, name="advancement-seating-set-layout"),
    path("seating/hold/", seating_hold, name="advancement-seating-hold"),
    path("seating/assign/", seating_assign, name="advancement-seating-assign"),
    # Stage 3: Sponsor impressions
    path("sponsorship/impressions/log/", sponsorship_log_impressions, name="advancement-impressions-log"),
    # Stage 3.1: Live availability + strict holds + purchase-held
    path("seating/availability/", seating_availability, name="advancement-seating-availability"),
    path("seating/hold-strict/", seating_hold_strict, name="advancement-seating-hold-strict"),
    path("seating/purchase-held/", seating_purchase_held, name="advancement-seating-purchase-held"),
    # Stage 3.2: Stripe Checkout + order status + webhook
    path("seating/checkout/", seating_checkout, name="advancement-seating-checkout"),
    path("orders/<uuid:order_id>/status/", order_status, name="advancement-order-status"),
    path("payments/stripe/webhook/", stripe_webhook, name="advancement-stripe-webhook"),
    # Stage 3.3: Section pricing + best-available checkout
    path("seating/best-available/checkout/", seating_best_available_checkout, name="advancement-best-available-checkout"),
    path("events/<uuid:event_id>/section-prices/", event_section_prices, name="advancement-section-prices"),
    # Stage 3.4: Sponsor placements + Wallet passes
    path("events/<uuid:event_id>/sponsors/", event_sponsors, name="advancement-event-sponsors"),
    path("wallet/apple/tickets/<uuid:ticket_id>.pkpass", apple_wallet_pass, name="advancement-apple-wallet-pass"),
    path("wallet/google/tickets/<uuid:ticket_id>/link/", google_wallet_link, name="advancement-google-wallet-link"),
    # ViewSet routes (CRUD + custom actions)
    path("", include(router.urls)),
]
