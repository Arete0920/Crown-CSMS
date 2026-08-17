from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import HouseholdFamilyLink, School
from core.permissions import user_has_permission
from crown_api.access_households import resolve_household_access
from crown_api.models import Message, MessageThread
from crown_api.serializers_comms import ThreadDetailSerializer, ThreadListSerializer
from tenants.tenant_context import get_request_school_id


def _require_auth_or_401(request):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response({"detail": "Authentication credentials were not provided."}, status=401)
    return None


def _request_school(request) -> School:
    school = getattr(request, "school", None)
    if school is not None:
        return school
    school_id = get_request_school_id(request, required=True)
    school = School.objects.filter(pk=school_id).first()
    if school is None:
        raise Http404()
    request.school = school
    return school


def _tenant_household_ids(school: School) -> set:
    return set(
        HouseholdFamilyLink.objects.filter(school=school).values_list("household_id", flat=True)
    )


def _authorized_threads(request):
    school = _request_school(request)
    tenant_households = _tenant_household_ids(school)
    access = resolve_household_access(request)
    qs = MessageThread.objects.select_related("household", "student")

    if user_has_permission(request.user, "communications.view", school=school):
        return qs.filter(household_id__in=tenant_households)

    if access.is_staff or access.person is None:
        raise PermissionDenied("Communications access is not authorized.")

    allowed = tenant_households.intersection(access.household_ids)
    return qs.filter(household_id__in=allowed)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def threads_list(request):
    unauth = _require_auth_or_401(request)
    if unauth is not None:
        return unauth
    qs = _authorized_threads(request).order_by("-last_message_at", "-updated_at")
    return Response(ThreadListSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def thread_detail(request, thread_id):
    unauth = _require_auth_or_401(request)
    if unauth is not None:
        return unauth
    qs = _authorized_threads(request)
    thread = get_object_or_404(qs, id=thread_id)
    recent_desc = list(
        Message.objects.filter(thread=thread)
        .select_related("sender_person")
        .order_by("-sent_at")[:25]
    )
    recent_chrono = list(reversed(recent_desc))
    return Response(ThreadDetailSerializer(thread, context={"messages": recent_chrono}).data)
