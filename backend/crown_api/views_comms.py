from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.models import Message, MessageThread
from crown_api.models_households import GUARDIAN_ROLES, HouseholdMember
from crown_api.models_identity import UserPersonLink
from crown_api.serializers_comms import ThreadDetailSerializer, ThreadListSerializer


def _authorized_household_ids(user):
    """Resolve family communication history from explicit identity linkage only."""
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    try:
        person = UserPersonLink.objects.select_related("person").get(user=user).person
    except UserPersonLink.DoesNotExist:
        return set()
    return set(
        HouseholdMember.objects.filter(person=person, role__in=GUARDIAN_ROLES)
        .values_list("household_id", flat=True)
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def threads_list(request):
    household_ids = _authorized_household_ids(request.user)
    if not household_ids:
        return Response([])
    qs = (
        MessageThread.objects.select_related("household", "student")
        .filter(household_id__in=household_ids)
        .order_by("-last_message_at", "-updated_at")
    )
    return Response(ThreadListSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def thread_detail(request, thread_id):
    household_ids = _authorized_household_ids(request.user)
    if not household_ids:
        raise Http404()
    thread = get_object_or_404(
        MessageThread.objects.select_related("household", "student").filter(
            household_id__in=household_ids
        ),
        id=thread_id,
    )
    recent_desc = list(
        Message.objects.filter(thread=thread)
        .select_related("sender_person")
        .order_by("-sent_at")[:25]
    )
    return Response(
        ThreadDetailSerializer(thread, context={"messages": list(reversed(recent_desc))}).data
    )
