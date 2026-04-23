from django.urls import path

from student_records.views import StudentRecordDetailView, StudentRecordListView

urlpatterns = [
    path("", StudentRecordListView.as_view(), name="student-records-list"),
    path("<uuid:student_id>/", StudentRecordDetailView.as_view(), name="student-records-detail"),
]