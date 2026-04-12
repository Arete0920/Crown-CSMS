from rest_framework import serializers

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)

from .schema_examples import (
    BOARD_PACK_RUN_REQUEST,
    BOARD_PACK_RUN_RESPONSE,
    BOARD_SCHEDULE_STATUS_RESPONSE,
    CROWN_COMPASS_RESPONSE,
    GOVERNANCE_DASHBOARD_RESPONSE,
    GOVERNANCE_METRICS_RESPONSE,
    HERITAGE_VERIFICATION_RESPONSE,
)

TENANT_HEADER_PARAMETER = OpenApiParameter(
    name="X-School-Id",
    type=str,
    location=OpenApiParameter.HEADER,
    required=True,
    description="Tenant school scope header. Governance endpoints also require authenticated users with the `board.view` permission.",
)

BOARD_PACKET_REQUEST_SERIALIZER = inline_serializer(
    name="BoardPacketRunRequest",
    fields={
        "meeting_date": serializers.DateField(required=False),
        "title": serializers.CharField(required=False, allow_blank=True),
    },
)

GOVERNANCE_SCHEDULE_RUN_SERIALIZER = inline_serializer(
    name="GovernanceScheduleRunRequest",
    fields={
        "meeting_date": serializers.DateField(required=False),
        "title": serializers.CharField(required=False, allow_blank=True),
    },
)

board_metrics_schema = extend_schema(
    tags=["Governance"],
    operation_id="governance_board_metrics",
    summary="Get governance board metrics",
    description="Returns the current governance metrics payload for the current school, including enrollment, finance-health, mission, and risk indicators. Any Discernment-style predictive references remain conceptual / hold-gated unless separately approved.",
    parameters=[TENANT_HEADER_PARAMETER],
    responses={
        200: OpenApiResponse(
            description="Live governance metrics payload.",
            examples=[OpenApiExample("Governance metrics example", value=GOVERNANCE_METRICS_RESPONSE, response_only=True)],
        )
    },
)

governance_dashboard_schema = extend_schema(
    tags=["Governance"],
    operation_id="governance_dashboard",
    summary="Get governance dashboard summary",
    description="Returns the current governance dashboard rollup for board review, including finance, enrollment, attendance, discipline, spiritual-life, and Crown Compass summary blocks. Any predictive insight remains conceptual / hold-gated unless separately approved.",
    parameters=[TENANT_HEADER_PARAMETER],
    responses={
        200: OpenApiResponse(
            description="Governance dashboard payload.",
            examples=[OpenApiExample("Governance dashboard example", value=GOVERNANCE_DASHBOARD_RESPONSE, response_only=True)],
        )
    },
)

crown_compass_schema = extend_schema(
    tags=["Crown Compass", "Governance"],
    operation_id="governance_crown_compass",
    summary="Get Crown Compass summary",
    description="Returns the current stored Crown Compass summary payload for the current school. Any Discernment predictive insight remains conceptual / hold-gated unless separately approved.",
    parameters=[TENANT_HEADER_PARAMETER],
    responses={
        200: OpenApiResponse(
            description="Current Crown Compass score payload.",
            examples=[OpenApiExample("Crown Compass example", value=CROWN_COMPASS_RESPONSE, response_only=True)],
        )
    },
)

board_packs_get_schema = extend_schema(
    methods=["GET"],
    tags=["Board Packs", "Board Delivery"],
    operation_id="governance_board_packs_list",
    summary="List recent board packs",
    description="Lists recent board packet artifacts for the current school. Returned packet metadata includes delivery-channel readiness details sourced from the live governance delivery layer.",
    parameters=[TENANT_HEADER_PARAMETER],
    responses={
        200: OpenApiResponse(
            description="Recent board pack list.",
            examples=[OpenApiExample("Board pack response example", value=[BOARD_PACK_RUN_RESPONSE], response_only=True)],
        )
    },
)

board_packs_post_schema = extend_schema(
    methods=["POST"],
    tags=["Board Packs", "Board Delivery"],
    operation_id="governance_board_packs_create",
    summary="Generate a live board pack",
    description="Creates a board packet from current live governance metrics and returns packet plus delivery-surface metadata for portal, email, Teams, and SharePoint review readiness.",
    parameters=[TENANT_HEADER_PARAMETER],
    request=BOARD_PACKET_REQUEST_SERIALIZER,
    responses={
        201: OpenApiResponse(
            description="Generated board pack payload.",
            examples=[
                OpenApiExample("Board pack request", value=BOARD_PACK_RUN_REQUEST, request_only=True),
                OpenApiExample("Board pack response", value=BOARD_PACK_RUN_RESPONSE, response_only=True),
            ],
        )
    },
)

board_pack_detail_schema = extend_schema(
    tags=["Board Packs", "Board Delivery"],
    operation_id="governance_board_pack_detail",
    summary="Get a board pack",
    description="Returns one previously generated board packet for the current school, including its section snapshot and delivery metadata.",
    parameters=[TENANT_HEADER_PARAMETER],
    responses={
        200: OpenApiResponse(
            description="Board pack detail payload.",
            examples=[OpenApiExample("Board pack detail example", value=BOARD_PACK_RUN_RESPONSE, response_only=True)],
        )
    },
)

governance_schedule_get_schema = extend_schema(
    methods=["GET"],
    tags=["Board Scheduling", "Board Delivery"],
    operation_id="governance_schedule_status",
    summary="Get board pack schedule status",
    description="Returns the current board-pack cadence, next run window, automation state, and delivery-channel readiness for the current school.",
    parameters=[TENANT_HEADER_PARAMETER],
    responses={
        200: OpenApiResponse(
            description="Board scheduling status payload.",
            examples=[OpenApiExample("Schedule status example", value=BOARD_SCHEDULE_STATUS_RESPONSE, response_only=True)],
        )
    },
)

governance_schedule_post_schema = extend_schema(
    methods=["POST"],
    tags=["Board Scheduling", "Board Delivery", "Board Packs"],
    operation_id="governance_schedule_run",
    summary="Run the scheduled board-pack job now",
    description="Triggers the live scheduled board-pack workflow for the current school and returns the created packet together with refreshed schedule state.",
    parameters=[TENANT_HEADER_PARAMETER],
    request=GOVERNANCE_SCHEDULE_RUN_SERIALIZER,
    responses={
        201: OpenApiResponse(
            description="Scheduled board-pack run result.",
            examples=[
                OpenApiExample("Schedule run request", value=BOARD_PACK_RUN_REQUEST, request_only=True),
                OpenApiExample(
                    "Schedule run response",
                    value={"status": "scheduled", "job": "board-pack-generation", "manual_only": False, "packet": BOARD_PACK_RUN_RESPONSE, "schedule": BOARD_SCHEDULE_STATUS_RESPONSE},
                    response_only=True,
                ),
            ],
        )
    },
)

heritage_governance_verification_schema = extend_schema(
    tags=["Governance"],
    operation_id="governance_heritage_verification",
    summary="Get governance release verification snapshot",
    description="Returns the governance release-readiness verification payload for current governance surfaces. Predictive or Discernment-style operationalization remains subject to separate approval.",
    parameters=[TENANT_HEADER_PARAMETER],
    responses={
        200: OpenApiResponse(
            description="Governance verification payload.",
            examples=[OpenApiExample("Verification example", value=HERITAGE_VERIFICATION_RESPONSE, response_only=True)],
        )
    },
)
