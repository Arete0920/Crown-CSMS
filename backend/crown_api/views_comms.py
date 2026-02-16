from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from crown_api.access_households import resolve_household_access
from crown_api.models import Message, MessageThread
from crown_api.serializers_comms import ThreadDetailSerializer, ThreadListSerializer


def _require_auth_or_401(request):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )
    return None


@api_view(["GET"])
@permission_classes([AllowAny])
def threads_list(request):
    unauth = _require_auth_or_401(request)
    if unauth is not None:
        return unauth

    access = resolve_household_access(request)

    qs = MessageThread.objects.select_related(
        "household",
        "student",
    )

    if not access.is_staff:
        qs = qs.filter(household_id__in=access.household_ids)

    qs = qs.order_by("-last_message_at", "-updated_at")
    return Response(ThreadListSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def thread_detail(request, thread_id):
    unauth = _require_auth_or_401(request)
    if unauth is not None:
        return unauth

    access = resolve_household_access(request)

    qs = MessageThread.objects.select_related(
        "household",
        "student",
    )

    if not access.is_staff:
        if not qs.filter(id=thread_id, household_id__in=access.household_ids).exists():
            raise Http404()
        qs = qs.filter(household_id__in=access.household_ids)

    thread = get_object_or_404(qs, id=thread_id)

    recent_desc = list(
        Message.objects.filter(thread=thread)
        .select_related("sender_person")
        .order_by("-sent_at")[:25]
    )
    recent_chrono = list(reversed(recent_desc))

    return Response(ThreadDetailSerializer(thread, context={"messages": recent_chrono}).data)
