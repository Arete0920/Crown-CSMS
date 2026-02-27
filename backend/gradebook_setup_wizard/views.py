from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from academics.models import AssignmentCategory, Section
from households.scoping import get_request_school_id

from .models import GradebookSetupWizardSession

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]


def _get_session(session_id, school_id):
    return get_object_or_404(GradebookSetupWizardSession, id=session_id, school__id=school_id)


def _validate_category(cat, idx):
    errors = []
    name = (cat.get("name") or "").strip()
    if not name:
        errors.append(f"categories[{idx}].name is required")
    try:
        w = Decimal(str(cat.get("weight_percent", 0)))
        if w < 0 or w > 100:
            errors.append(f"categories[{idx}].weight_percent must be 0-100")
    except Exception:
        errors.append(f"categories[{idx}].weight_percent must be a number")
    return errors


# ---------------------------------------------------------------------------
# 1. Create
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)
    session = GradebookSetupWizardSession.objects.create(
        school=school,
        created_by=request.user if request.user.is_authenticated else None,
    )
    return Response({"session_id": str(session.id), "status": session.status}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# 2. Configure (section_id)
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    import uuid as _uuid
    section_id_raw = request.data.get("section_id")
    if not section_id_raw:
        return Response({"error": "section_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        section_uuid = _uuid.UUID(str(section_id_raw))
    except (ValueError, AttributeError):
        return Response({"error": "section_id must be a valid UUID"}, status=status.HTTP_400_BAD_REQUEST)

    # Verify section belongs to this school
    get_object_or_404(Section, id=section_uuid, school_id=school_id)

    session.section_id = section_uuid
    session.status = GradebookSetupWizardSession.STATUS_CONFIGURED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status, "section_id": str(section_uuid)})


# ---------------------------------------------------------------------------
# 3. Define categories
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def define_categories(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        GradebookSetupWizardSession.STATUS_CONFIGURED,
        GradebookSetupWizardSession.STATUS_CATEGORIES_DEFINED,
    ):
        return Response(
            {"error": f"Cannot define categories from status '{session.status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cats_raw = request.data.get("categories")
    if not isinstance(cats_raw, list) or len(cats_raw) == 0:
        return Response({"error": "categories must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    errors = []
    for idx, c in enumerate(cats_raw):
        errors.extend(_validate_category(c, idx))
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    total = sum(Decimal(str(c.get("weight_percent", 0))) for c in cats_raw)
    if total not in (Decimal("0"), Decimal("100")):
        return Response(
            {"error": f"Category weights must sum to 0 (unweighted) or 100 (weighted). Got {total}."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cleaned = [
        {
            "name": c["name"].strip(),
            "weight_percent": float(Decimal(str(c.get("weight_percent", 0)))),
            "sort_order": int(c.get("sort_order", idx)),
        }
        for idx, c in enumerate(cats_raw)
    ]

    session.categories = cleaned
    session.status = GradebookSetupWizardSession.STATUS_CATEGORIES_DEFINED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status, "category_count": len(cleaned), "total_weight": float(total)})


# ---------------------------------------------------------------------------
# 4. Commit — create/update AssignmentCategory records
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        GradebookSetupWizardSession.STATUS_CATEGORIES_DEFINED,
        GradebookSetupWizardSession.STATUS_COMMITTED,
    ):
        return Response(
            {"error": f"Cannot commit from status '{session.status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not request.data.get("confirm"):
        return Response({"error": "confirm is required"}, status=status.HTTP_400_BAD_REQUEST)

    section = get_object_or_404(Section, id=session.section_id, school_id=school_id)

    created_count = 0
    updated_count = 0

    with transaction.atomic():
        for cat in session.categories:
            obj, created = AssignmentCategory.objects.get_or_create(
                section=section,
                name=cat["name"],
                defaults={
                    "school_id": school_id,
                    "weight_percent": cat["weight_percent"],
                    "sort_order": cat["sort_order"],
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
            else:
                obj.weight_percent = cat["weight_percent"]
                obj.sort_order = cat["sort_order"]
                obj.save(update_fields=["weight_percent", "sort_order", "updated_at"])
                updated_count += 1

        result = {
            "categories_created": created_count,
            "categories_updated": updated_count,
            "total": created_count + updated_count,
        }
        session.commit_result = result
        session.status = GradebookSetupWizardSession.STATUS_COMMITTED
        session.save()

    return Response({"status": session.status, **result})


# ---------------------------------------------------------------------------
# 5. Verify
# ---------------------------------------------------------------------------

@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        GradebookSetupWizardSession.STATUS_COMMITTED,
        GradebookSetupWizardSession.STATUS_VERIFIED,
    ):
        return Response(
            {"error": f"Cannot verify from status '{session.status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cat_count = AssignmentCategory.objects.filter(
        section_id=session.section_id, school_id=school_id, is_active=True
    ).count()

    session.status = GradebookSetupWizardSession.STATUS_VERIFIED
    session.save()

    return Response({
        "status": session.status,
        "category_count": cat_count,
        "section_id": str(session.section_id),
        "commit_result": session.commit_result,
    })
