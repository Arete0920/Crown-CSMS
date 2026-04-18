from django.urls import path
from .views import GraduationAuditView
from .views_breakdown import GraduationAuditBreakdownView

urlpatterns = [
    path("audit/<uuid:student_id>/", GraduationAuditView.as_view(), name="graduation-audit"),
    path("audit/<uuid:student_id>/breakdown/", GraduationAuditBreakdownView.as_view(), name="graduation-audit-breakdown"),
]
