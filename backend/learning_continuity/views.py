from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .contracts import CROWN_AUTHORITY_RULES, get_learning_continuity_page


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def learning_continuity_page(request, page_key: str):
    """
    CROWN source-of-truth contract endpoint.

    Microsoft, Teams, SDS, Graph, providers, and manual imports are execution or
    signal sources. CROWN remains the school process/data authority.
    """
    page = get_learning_continuity_page(page_key)
    if page is None:
        return Response(
            {
                "detail": f"Unknown learning continuity page '{page_key}'.",
                "code": "unknown_learning_continuity_page",
            },
            status=404,
        )

    return Response(
        {
            "authorityRules": CROWN_AUTHORITY_RULES,
            **page,
        }
    )
