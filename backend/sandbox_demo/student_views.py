from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .student_self_service import SandboxStudentError, student_self_service_state


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sandbox_student_self_service(request):
    try:
        return Response(student_self_service_state(request.user))
    except SandboxStudentError as exc:
        return Response({"detail": str(exc)}, status=403)
