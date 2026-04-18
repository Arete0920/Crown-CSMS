from django.urls import path
from . import views

urlpatterns = [
    path("api/v1/release-closeout/status/", views.release_status, name="release-closeout-status"),
    path("api/v1/release-closeout/metrics/live/", views.metrics_live, name="release-closeout-metrics-live"),
    path("api/v1/release-closeout/graduation/<str:student_ref>/", views.graduation_status, name="release-closeout-graduation"),
    path("api/v1/release-closeout/discipline/<str:student_ref>/", views.discipline_escalation, name="release-closeout-discipline"),
    path("api/v1/reports/transcript/<str:student_ref>/", views.transcript_pdf, name="report-transcript"),
    path("api/v1/reports/report-card/<str:student_ref>/", views.report_card_pdf, name="report-report-card"),
    path("api/v1/reports/discipline/<str:student_ref>/", views.discipline_pdf, name="report-discipline"),
    path("api/v1/reports/board/", views.board_pdf, name="report-board"),
    path("api/v1/notifications/sms/status/", views.sms_status, name="notifications-sms-status"),
]
