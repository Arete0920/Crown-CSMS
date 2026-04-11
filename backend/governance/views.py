from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def governance_dashboard(request):
    """School-board governance dashboard summary."""
    return Response({}, status=status.HTTP_200_OK)
