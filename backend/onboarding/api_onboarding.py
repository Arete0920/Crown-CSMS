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
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from households.scoping import get_request_school_id
from onboarding.models_tasks import OnboardingTask, HelpArticle, can_activate_school, seed_onboarding_tasks
from core.models import School


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def onboarding_progress(request, school_id):
    """Return setup completion statistics for the given school."""
    # Tenant gate: caller must belong to the requested school
    caller_school_id = get_request_school_id(request)
    if str(caller_school_id) != str(school_id):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    try:
        school = School.objects.get(pk=school_id)
    except School.DoesNotExist:
        return Response({"detail": "School not found."}, status=status.HTTP_404_NOT_FOUND)

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
        return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

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
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    try:
        school = School.objects.get(pk=school_id)
    except School.DoesNotExist:
        return Response({"detail": "School not found."}, status=status.HTTP_404_NOT_FOUND)

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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def help_article(request, slug):
    """Return a contextual help article by slug."""
    try:
        article = HelpArticle.objects.get(slug=slug, published=True)
    except HelpArticle.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "slug": article.slug,
        "title": article.title,
        "content": article.content,
        "module": article.module,
    })
