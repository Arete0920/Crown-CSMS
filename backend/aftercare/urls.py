from django.urls import path
from . import api, wizard_api

urlpatterns = [
    # Program setup
    path("config/",                                      api.program_config,           name="aftercare_config"),
    path("wizard/setup/",                                wizard_api.aftercare_setup_wizard, name="aftercare_setup_wizard"),

    # Enrollment
    path("enrollments/",                                 api.enrollments,              name="aftercare_enrollments"),

    # Pickup contacts per student
    path("students/<int:student_id>/pickup-contacts/",   api.pickup_contacts,          name="aftercare_pickup_contacts"),

    # Roster + check-in/out
    path("roster/today/",                                api.roster_today,             name="aftercare_roster_today"),
    path("attendance/checkin/",                          api.checkin,                  name="aftercare_checkin"),
    path("attendance/checkout/",                         api.checkout,                 name="aftercare_checkout"),

    # Incidents
    path("incidents/",                                   api.incidents,                name="aftercare_incidents"),

    # Parent portal (read-only)
    path("parent/<int:student_id>/",                     api.parent_view,              name="aftercare_parent_view"),

    # Board governance summary
    path("board/summary/",                               api.board_summary,            name="aftercare_board_summary"),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
