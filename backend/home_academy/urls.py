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
        "offering-enrollments/<int:registration_id>/complete/",
        api.complete_offering_enrollment,
        name="home-academy-offering-enrollment-complete",
    ),
    path(
        "offering-enrollments/<int:registration_id>/post-transcript/",
        api.post_offering_transcript,
        name="home-academy-offering-enrollment-post-transcript",
    ),
    path(
        "offerings/<int:offering_id>/students/<uuid:student_id>/eligibility/",
        api.offering_eligibility,
        name="home-academy-offering-eligibility",
    ),
    path("financial-aid-rules/", api.financial_aid_rules, name="home-academy-financial-aid-rules"),
    path("parent/summary/", api.parent_summary, name="home-academy-parent-summary"),
    path("board/summary/", api.board_summary, name="home-academy-board-summary"),
]
