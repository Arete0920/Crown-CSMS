from django.urls import path

from . import api, wizard_api

urlpatterns = [
    path("config/", api.program_config, name="aftercare_config"),
    path("wizard/setup/", wizard_api.aftercare_setup_wizard, name="aftercare_setup_wizard"),
    path("enrollments/", api.enrollments, name="aftercare_enrollments"),
    path("students/<uuid:student_id>/pickup-contacts/", api.pickup_contacts, name="aftercare_pickup_contacts"),
    path("roster/today/", api.roster_today, name="aftercare_roster_today"),
    path("attendance/checkin/", api.checkin, name="aftercare_checkin"),
    path("attendance/checkout/", api.checkout, name="aftercare_checkout"),
    path("incidents/", api.incidents, name="aftercare_incidents"),
    path("parent/<uuid:student_id>/", api.parent_view, name="aftercare_parent_view"),
    path("board/summary/", api.board_summary, name="aftercare_board_summary"),
]
