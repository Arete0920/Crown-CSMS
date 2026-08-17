from django.urls import path

from student_records.permissions import CanViewStudentRecords
from student_records.views import StudentRecordDetailView, StudentRecordListView


STUDENT_RECORD_PERMISSIONS = [CanViewStudentRecords]

urlpatterns = [
    path(
        "",
        StudentRecordListView.as_view(permission_classes=STUDENT_RECORD_PERMISSIONS),
        name="student-records-list",
    ),
    path(
        "<uuid:student_id>/",
        StudentRecordDetailView.as_view(permission_classes=STUDENT_RECORD_PERMISSIONS),
        name="student-records-detail",
    ),
]
