"""Read-only SOLOMON API endpoints."""

from __future__ import annotations

from django.http import Http404, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import solomon_api_enabled, can_access_governance_queue
from .serializers import (
    SolomonAudienceSerializer,
    SolomonCategorySerializer,
    SolomonContextResponseSerializer,
    SolomonPlaybookSerializer,
    SolomonResourceSerializer,
    SolomonTopicSerializer,
)
from .services import (
    SolomonContextResolver,
    governance_filtered_review_queue,
    governance_review_queue,
    visible_audiences,
    visible_categories,
    visible_playbooks,
    visible_resources,
    visible_topics,
)


def _require_solomon_api_enabled():
    if not solomon_api_enabled():
        raise Http404


def _query_params(request):
    return getattr(request, "query_params", request.GET)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def categories_list(request):
    _require_solomon_api_enabled()
    queryset = visible_categories(request)
    serializer = SolomonCategorySerializer(queryset, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def topics_list(request):
    _require_solomon_api_enabled()
    queryset = visible_topics(request)
    serializer = SolomonTopicSerializer(queryset, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def audiences_list(request):
    _require_solomon_api_enabled()
    queryset = visible_audiences(request)
    serializer = SolomonAudienceSerializer(queryset, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def resources_list(request):
    _require_solomon_api_enabled()
    params = _query_params(request)
    queryset = visible_resources(
        request,
        module=params.get("module", ""),
        route=params.get("route", ""),
        audience=params.get("audience", ""),
        scope=params.get("scope", ""),
    )
    serializer = SolomonResourceSerializer(queryset, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def playbooks_list(request):
    _require_solomon_api_enabled()
    params = _query_params(request)
    queryset = visible_playbooks(
        request,
        module=params.get("module", ""),
        route=params.get("route", ""),
        audience=params.get("audience", ""),
    )
    serializer = SolomonPlaybookSerializer(queryset, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def context_view(request):
    _require_solomon_api_enabled()
    params = _query_params(request)
    resolver = SolomonContextResolver(
        request=request,
        module=params.get("module", ""),
        route=params.get("route", ""),
        audience=params.get("audience", ""),
        scope=params.get("scope", ""),
    )
    payload = resolver.resolve()
    serializer = SolomonContextResponseSerializer(payload, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def review_queue(request):
	"""
	Governance review queue: resources in DRAFT or APPROVED state.

	Query params:
	- status: comma-separated filter (draft,approved). Invalid values return empty list (fail-closed).

	Requires staff/admin access.
	"""
	_require_solomon_api_enabled()
	if not can_access_governance_queue(request):
		raise Http404

	params = _query_params(request)
	status_filter = params.get("status", "").strip()

	if status_filter:
		queryset = governance_filtered_review_queue(request, status_filter)
	else:
		queryset = governance_review_queue(request)

	serializer = SolomonResourceSerializer(queryset, many=True, context={"request": request})
	return Response(serializer.data)


def solomon_status(request):
    return JsonResponse(
        {
            "module": "solomon",
            "status": "scaffold",
            "implementation": "not_started",
        }
    )
