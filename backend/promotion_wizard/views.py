from __future__ import annotations

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from households.scoping import get_request_school_id
from core.models import School
from promotion_wizard.models import PromotionRule, PromotionWizardSession, VALID_GRADE_CODES
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]


def _get_session(session_id, school_id):
    return get_object_or_404(PromotionWizardSession, id=session_id, school__id=school_id)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    school = get_object_or_404(School, id=school_id)
    sess = PromotionWizardSession.objects.create(school=school)
    return Response({"session_id": str(sess.id), "status": sess.status}, status=status.HTTP_201_CREATED)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure(request, session_id):
    school_id = get_request_school_id(request)
    sess = _get_session(session_id, school_id)

    if sess.status != "draft":
        return Response({"error": "Session not in draft state"}, status=status.HTTP_400_BAD_REQUEST)

    rules = request.data.get("rules")
    if not isinstance(rules, list) or not rules:
        return Response({"error": "rules must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    normalized = []
    seen_from = set()
    for i, row in enumerate(rules):
        if not isinstance(row, dict):
            return Response({"error": f"rules[{i}] must be an object"}, status=status.HTTP_400_BAD_REQUEST)
        frm = str(row.get("from_grade_code", "")).strip().upper()
        to = str(row.get("to_grade_code", "")).strip().upper()
        if frm not in VALID_GRADE_CODES:
            return Response({"error": f"rules[{i}].from_grade_code invalid"}, status=status.HTTP_400_BAD_REQUEST)
        if to not in VALID_GRADE_CODES:
            return Response({"error": f"rules[{i}].to_grade_code invalid"}, status=status.HTTP_400_BAD_REQUEST)
        if frm in seen_from:
            return Response({"error": f"Duplicate from_grade_code: {frm}"}, status=status.HTTP_400_BAD_REQUEST)
        seen_from.add(frm)
        normalized.append({
            "from_grade_code": frm,
            "to_grade_code": to,
            "ordering": int(row.get("ordering", i)),
        })

    sess.rules = normalized
    sess.status = "configured"
    sess.save(update_fields=["rules", "status"])
    return Response({"status": sess.status, "count": len(normalized)})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit(request, session_id):
    school_id = get_request_school_id(request)
    sess = _get_session(session_id, school_id)

    if sess.status != "configured":
        return Response({"error": "Commit requires configured state"}, status=status.HTTP_400_BAD_REQUEST)

    created = 0
    updated = 0
    keep = [r["from_grade_code"] for r in sess.rules or []]

    with transaction.atomic():
        for row in sess.rules or []:
            _, was_created = PromotionRule.objects.update_or_create(
                school_id=sess.school_id,
                from_grade_code=row["from_grade_code"],
                defaults={"to_grade_code": row["to_grade_code"], "ordering": row.get("ordering", 0)},
            )
            created += 1 if was_created else 0
            updated += 0 if was_created else 1

        PromotionRule.objects.filter(school_id=sess.school_id).exclude(from_grade_code__in=keep).delete()

        sess.commit_result = {"created": created, "updated": updated, "total": len(keep)}
        sess.status = "committed"
        sess.save(update_fields=["commit_result", "status"])

    return Response({"status": sess.status, **sess.commit_result})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify(request, session_id):
    school_id = get_request_school_id(request)
    sess = _get_session(session_id, school_id)

    if sess.status not in ("committed", "verified"):
        return Response({"error": "Verify requires committed state"}, status=status.HTTP_400_BAD_REQUEST)

    rules = list(
        PromotionRule.objects.filter(school_id=sess.school_id)
        .values("from_grade_code", "to_grade_code", "ordering")
        .order_by("ordering", "from_grade_code")
    )
    sess.status = "verified"
    sess.save(update_fields=["status"])
    return Response({"status": sess.status, "rules": rules, "count": len(rules)})
