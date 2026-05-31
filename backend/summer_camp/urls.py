from django.urls import path

from . import api, wizard_api


urlpatterns = [
    path("config/", api.config_view, name="summer_camp_config"),
    path("wizard/setup/", wizard_api.summer_camp_setup_wizard, name="summer_camp_setup_wizard"),

    path("programs/", api.programs_view, name="summer_camp_programs"),
    path("programs/<int:program_id>/", api.program_detail_view, name="summer_camp_program_detail"),

    path("sessions/", api.sessions_view, name="summer_camp_sessions"),
    path("sessions/<int:session_id>/", api.session_detail_view, name="summer_camp_session_detail"),
    path("sessions/<int:session_id>/roster/", api.session_roster_view, name="summer_camp_session_roster"),

    path("enrollments/", api.enrollments_view, name="summer_camp_enrollments"),

    path("roster/today/", api.roster_today_view, name="summer_camp_roster_today"),
    path("attendance/checkin/", api.attendance_checkin_view, name="summer_camp_attendance_checkin"),
    path("attendance/checkout/", api.attendance_checkout_view, name="summer_camp_attendance_checkout"),

    path("incidents/", api.incidents_view, name="summer_camp_incidents"),

    path("forms/missing/", api.missing_forms_view, name="summer_camp_forms_missing"),
    path("health/review-queue/", api.health_review_queue_view, name="summer_camp_health_review_queue"),

    path("parent/<uuid:student_id>/", api.parent_student_view, name="summer_camp_parent_student"),
    path("board/summary/", api.board_summary_view, name="summer_camp_board_summary"),
]
