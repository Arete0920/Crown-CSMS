from django.urls import path
from .views import GraduationAuditView

urlpatterns = [
    path("audit/<uuid:student_id>/", GraduationAuditView.as_view(), name="graduation-audit"),
]
