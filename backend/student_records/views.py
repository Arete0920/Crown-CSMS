from rest_framework import generics

from core.models import Student
from core.permissions import CrownModulePermission
from tenants.tenant_context import get_request_school_id

from .serializers import StudentRecordSerializer


class StudentRecordListView(generics.ListAPIView):
    permission_classes = [CrownModulePermission("registrar.view")]
    serializer_class = StudentRecordSerializer

    def get_queryset(self):
        school_id = get_request_school_id(self.request, required=True)
        return Student.objects.filter(school_id=school_id).order_by("last_name", "first_name")


class StudentRecordDetailView(generics.RetrieveAPIView):
    permission_classes = [CrownModulePermission("registrar.view")]
    serializer_class = StudentRecordSerializer
    lookup_url_kwarg = "student_id"

    def get_queryset(self):
        school_id = get_request_school_id(self.request, required=True)
        return Student.objects.filter(school_id=school_id)
