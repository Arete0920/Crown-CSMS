from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema


def schema_object(summary: str = "", description: str = ""):
    return extend_schema(
        summary=summary or None,
        description=description or None,
        responses={200: OpenApiTypes.OBJECT},
    )


def schema_list(summary: str = "", description: str = ""):
    return extend_schema(
        summary=summary or None,
        description=description or None,
        responses={200: OpenApiTypes.OBJECT},
    )


def schema_created(summary: str = "", description: str = ""):
    return extend_schema(
        summary=summary or None,
        description=description or None,
        responses={201: OpenApiTypes.OBJECT},
    )


def schema_excluded():
    return extend_schema(exclude=True)


GENERIC_JSON_RESPONSE = OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description="Generic object response",
)