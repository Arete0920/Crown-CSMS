from django.urls import include, path
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
    pledge_create,
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
    moves_transition,
    seating_set_layout,
    seating_hold,
    seating_assign,
    sponsorship_log_impressions,
    seating_availability,
    seating_hold_strict,
    event_section_prices,
    event_sponsors,
    apple_wallet_pass,
    google_wallet_link,
)
from .secure_views import advancement_summary, pledge_cancel, qr_checkin
from .payment_hold_views import (
    advancement_edit_post_payment_on_hold,
    advancement_view_get_payment_on_hold,
    advancement_view_post_payment_on_hold,
    authenticated_post_payment_on_hold,
    provider_webhook_not_configured,
)

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r"donors", DonorViewSet, basename="advancement-donors")
router.register(r"campaigns", CampaignViewSet, basename="advancement-campaigns")
router.register(r"sponsorships", SponsorshipPackageViewSet, basename="advancement-sponsorships")
router.register(r"events", EventViewSet, basename="advancement-events")
router.register(r"tickets", TicketViewSet, basename="advancement-tickets")
router.register(r"store", StoreItemViewSet, basename="advancement-store")
router.register(r"gifts", GiftViewSet, basename="advancement-gifts")
router.register(r"pledges-list", PledgeViewSet, basename="advancement-pledges-list")
router.register(r"agreements", SponsorshipAgreementViewSet, basename="advancement-agreements")
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
    path("summary/", advancement_summary, name="advancement-summary"),
    path("metrics/", advancement_metrics, name="advancement-metrics"),
    path("purchase/ticket/", authenticated_post_payment_on_hold, name="advancement-purchase-ticket"),
    path("purchase/store/", authenticated_post_payment_on_hold, name="advancement-purchase-store"),
    path("gift/checkout/", authenticated_post_payment_on_hold, name="advancement-gift-checkout"),
    path("gift/<uuid:gift_id>/mark-paid/", authenticated_post_payment_on_hold, name="advancement-gift-mark-paid"),
    path("pledges/create/", pledge_create, name="advancement-pledge-create"),
    path("pledges/<uuid:pledge_id>/cancel/", pledge_cancel, name="advancement-pledge-cancel"),
    path("sponsorship/checkout/", authenticated_post_payment_on_hold, name="advancement-sponsorship-checkout"),
    path("sponsorship/<uuid:agreement_id>/mark-paid/", authenticated_post_payment_on_hold, name="advancement-sponsorship-mark-paid"),
    path("qr-checkin/", qr_checkin, name="advancement-qr-checkin"),
    path("moves/transition/", moves_transition, name="advancement-moves-transition"),
    path("seating/set-layout/", seating_set_layout, name="advancement-seating-set-layout"),
    path("seating/hold/", seating_hold, name="advancement-seating-hold"),
    path("seating/assign/", seating_assign, name="advancement-seating-assign"),
    path("sponsorship/impressions/log/", sponsorship_log_impressions, name="advancement-impressions-log"),
    path("seating/availability/", seating_availability, name="advancement-seating-availability"),
    path("seating/hold-strict/", seating_hold_strict, name="advancement-seating-hold-strict"),
    path("seating/purchase-held/", advancement_edit_post_payment_on_hold, name="advancement-seating-purchase-held"),
    path("seating/checkout/", advancement_view_post_payment_on_hold, name="advancement-seating-checkout"),
    path("orders/<uuid:order_id>/status/", advancement_view_get_payment_on_hold, name="advancement-order-status"),
    path("payments/stripe/webhook/", provider_webhook_not_configured, name="advancement-stripe-webhook"),
    path("seating/best-available/checkout/", advancement_view_post_payment_on_hold, name="advancement-best-available-checkout"),
    path("events/<uuid:event_id>/section-prices/", event_section_prices, name="advancement-section-prices"),
    path("events/<uuid:event_id>/sponsors/", event_sponsors, name="advancement-event-sponsors"),
    path("wallet/apple/tickets/<uuid:ticket_id>.pkpass", apple_wallet_pass, name="advancement-apple-wallet-pass"),
    path("wallet/google/tickets/<uuid:ticket_id>/link/", google_wallet_link, name="advancement-google-wallet-link"),
    path("", include(router.urls)),
]
