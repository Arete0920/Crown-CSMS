from django.http import JsonResponse
from django.utils import timezone
from .permissions import require_roles


@require_roles(["admin", "finance"])
def finance_guardrail_proof(request):
    """
    Proof endpoint: demonstrates RBAC enforcement.
    """
    return JsonResponse(
        {
            "ok": True,
            "ts": timezone.now().isoformat(),
            "message": "RBAC OK: you are allowed to access finance guardrail proof.",
        }
    )
