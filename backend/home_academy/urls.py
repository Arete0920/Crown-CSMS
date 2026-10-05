from django.urls import path

from . import api

urlpatterns = [
    path("config/", api.program_config, name="home-academy-config"),
    path("enrollments/", api.enrollments, name="home-academy-enrollments"),
    path("offerings/", api.offerings, name="home-academy-offerings"),
    path("offering-enrollments/", api.offering_enrollments, name="home-academy-offering-enrollments"),
    path(
        "offering-enrollments/<int:registration_id>/activate/",
        api.activate_offering_enrollment,
        name="home-academy-offering-enrollment-activate",
    ),
    path(
        "offerings/<int:offering_id>/students/<uuid:student_id>/eligibility/",
        api.offering_eligibility,
        name="home-academy-offering-eligibility",
    ),
    path("financial-aid-rules/", api.financial_aid_rules, name="home-academy-financial-aid-rules"),
    path("board/summary/", api.board_summary, name="home-academy-board-summary"),
]
