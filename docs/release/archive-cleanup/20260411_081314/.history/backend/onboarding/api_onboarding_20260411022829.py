"""
onboarding/api_onboarding.py

Stage 3 onboarding + setup-progress endpoints:

  GET  /api/v1/onboarding/<school_id>/progress/   — setup completion stats
  POST /api/v1/onboarding/<school_id>/tasks/<id>/complete/ — mark task done
  GET  /api/v1/onboarding/<school_id>/can-activate/ — activation gate
  GET  /api/v1/help/<slug>/                         — contextual help article
"""
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from core.models import School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id
from onboarding.models_tasks import (
    HelpArticle,
    OnboardingTask,
    SolomonAudience,
    SolomonCategory,
    SolomonTopic,
    can_activate_school,
    seed_onboarding_tasks,
)
from onboarding.solomon_seed import ensure_solomon_seed_data
from onboarding.solomon_services import get_contextual_solomon_help, search_solomon_content

FORBIDDEN_DETAIL = "Forbidden."
NOT_FOUND_DETAIL = "Not found."
SCHOOL_NOT_FOUND_DETAIL = "School not found."
TASK_NOT_FOUND_DETAIL = "Task not found."


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def onboarding_progress(request, school_id):
    """Return setup completion statistics for the given school."""
    # Tenant gate: caller must belong to the requested school
    caller_school_id = get_request_school_id(request)
    if str(caller_school_id) != str(school_id):
        return Response({"detail": FORBIDDEN_DETAIL}, status=status.HTTP_403_FORBIDDEN)

    try:
        school = School.objects.get(pk=school_id)
    except School.DoesNotExist:
        return Response({"detail": SCHOOL_NOT_FOUND_DETAIL}, status=status.HTTP_404_NOT_FOUND)

    tasks = OnboardingTask.objects.filter(school=school)
    if not tasks.exists():
        seed_onboarding_tasks(school)
        tasks = OnboardingTask.objects.filter(school=school)

    total = tasks.count()
    completed = tasks.filter(status=OnboardingTask.STATUS_COMPLETE).count()

    return Response({
        "school_id": str(school_id),
        "total_tasks": total,
        "completed": completed,
        "percent_complete": round((completed / total) * 100 if total else 0, 2),
        "tasks": list(tasks.values("id", "task_name", "status", "order", "completed_at")),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_task_complete(request, school_id, task_id):
    """Mark a single onboarding task as complete."""
    caller_school_id = get_request_school_id(request)
    if str(caller_school_id) != str(school_id):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    try:
        task = OnboardingTask.objects.get(pk=task_id, school_id=school_id)
    except OnboardingTask.DoesNotExist:
        return Response({"detail": TASK_NOT_FOUND_DETAIL}, status=status.HTTP_404_NOT_FOUND)

    task.status = OnboardingTask.STATUS_COMPLETE
    task.completed_at = timezone.now()
    task.save(update_fields=["status", "completed_at"])

    return Response({"id": task.id, "status": task.status, "completed_at": task.completed_at})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def activation_gate(request, school_id):
    """Return whether this school has completed all onboarding tasks."""
    caller_school_id = get_request_school_id(request)
    if str(caller_school_id) != str(school_id):
        return Response({"detail": FORBIDDEN_DETAIL}, status=status.HTTP_403_FORBIDDEN)

    try:
        school = School.objects.get(pk=school_id)
    except School.DoesNotExist:
        return Response({"detail": SCHOOL_NOT_FOUND_DETAIL}, status=status.HTTP_404_NOT_FOUND)

    ready = can_activate_school(school)
    pending = list(
        OnboardingTask.objects.filter(school=school, status=OnboardingTask.STATUS_PENDING)
        .values_list("task_name", flat=True)
    )

    return Response({
        "school_id": str(school_id),
        "can_activate": ready,
        "pending_tasks": pending,
    })


def _can_manage_solomon(user) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return bool(
        getattr(user, "is_staff", False)
        or getattr(user, "is_superuser", False)
        or user_has_permission(user, "admin.view")
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def help_article(request, slug):
    """Return a public or request-visible help article by slug."""
    payload = get_contextual_solomon_help(request, slug=slug)
    article = payload.get("primary_article")
    if not article:
        return Response({"detail": NOT_FOUND_DETAIL}, status=status.HTTP_404_NOT_FOUND)

    return Response(article)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def solomon_articles(request):
    """Public search/list surface plus authenticated authoring entrypoint."""
    if request.method == "GET":
        payload = search_solomon_content(
            request,
            query=request.query_params.get("q", ""),
            module=request.query_params.get("module", ""),
            audience=request.query_params.get("audience", ""),
        )
        return Response(payload)

    if not _can_manage_solomon(request.user):
        return Response({"detail": FORBIDDEN_DETAIL}, status=status.HTTP_403_FORBIDDEN)

    ensure_solomon_seed_data()
    category = None
    category_slug = request.data.get("category_slug") or ""
    if category_slug:
        category = SolomonCategory.objects.filter(slug=category_slug).first()

    article, _ = HelpArticle.objects.update_or_create(
        slug=request.data.get("slug", ""),
        defaults={
            "title": request.data.get("title", ""),
            "summary": request.data.get("summary", ""),
            "content": request.data.get("content", ""),
            "module": request.data.get("module", "solomon"),
            "article_type": request.data.get("article_type", HelpArticle.TYPE_GUIDE),
            "visibility": request.data.get("visibility", HelpArticle.VISIBILITY_AUTHENTICATED),
            "state": request.data.get("state", HelpArticle.STATE_PUBLISHED),
            "category": category,
            "route_path": request.data.get("route_path", ""),
            "published": request.data.get("state", HelpArticle.STATE_PUBLISHED) == HelpArticle.STATE_PUBLISHED,
        },
    )

    topic_slugs = request.data.get("topics") or []
    if isinstance(topic_slugs, list):
        article.topics.set(list(SolomonTopic.objects.filter(slug__in=topic_slugs)))

    audience_slugs = request.data.get("audiences") or []
    if isinstance(audience_slugs, list):
        article.audiences.set(list(SolomonAudience.objects.filter(slug__in=audience_slugs)))

    return Response(
        {
            "id": article.pk,
            "slug": article.slug,
            "title": article.title,
            "state": article.state,
            "published": article.published,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def solomon_article_detail(request, slug):
    payload = get_contextual_solomon_help(request, slug=slug)
    article = payload.get("primary_article")
    if not article:
        return Response({"detail": NOT_FOUND_DETAIL}, status=status.HTTP_404_NOT_FOUND)
    return Response(article)


@api_view(["GET"])
@permission_classes([AllowAny])
def solomon_context(request):
    payload = get_contextual_solomon_help(
        request,
        slug=request.query_params.get("slug", ""),
        route_path=request.query_params.get("route_path", ""),
        module=request.query_params.get("module", ""),
        audience=request.query_params.get("audience", ""),
        context_key=request.query_params.get("context_key", ""),
    )
    if not payload.get("primary_article") and not payload.get("playbooks"):
        return Response({"detail": NOT_FOUND_DETAIL}, status=status.HTTP_404_NOT_FOUND)
    return Response(payload)


@api_view(["GET"])
@permission_classes([AllowAny])
def solomon_categories(request):
    payload = search_solomon_content(request)
    return Response({"categories": payload.get("categories", [])})


@api_view(["GET"])
@permission_classes([AllowAny])
def solomon_playbooks(request):
    payload = search_solomon_content(
        request,
        query=request.query_params.get("q", ""),
        module=request.query_params.get("module", ""),
        audience=request.query_params.get("audience", ""),
    )
    return Response({"playbooks": payload.get("playbooks", [])})


@api_view(["GET"])
@permission_classes([AllowAny])
def solomon_search(request):
    payload = search_solomon_content(
        request,
        query=request.query_params.get("q", ""),
        module=request.query_params.get("module", ""),
        audience=request.query_params.get("audience", ""),
    )
    return Response(payload)
