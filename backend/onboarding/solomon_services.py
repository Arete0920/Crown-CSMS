"""
onboarding/solomon_services.py

Service layer for Solomon contextual help and content search.
"""
from django.conf import settings
from onboarding.models_tasks import HelpArticle, SolomonPlaybook
from django.db.models import Q
from typing import Any, cast
from solomon.adapters import OnboardingAdapter, SolomonContextRequest


HELP_ARTICLE_MANAGER = cast(Any, HelpArticle).objects
SOLOMON_PLAYBOOK_MANAGER = cast(Any, SolomonPlaybook).objects

SOLOMON_CONTEXT_ALLOWED_STATUSES = {"resolved", "empty", "disabled", "error"}


def _visibility_qs(request):
    """Return a Q filter that limits articles to what this request can see."""
    user = getattr(request, "user", None)
    is_authenticated = bool(user and getattr(user, "is_authenticated", False))
    is_staff = is_authenticated and bool(getattr(user, "is_staff", False))
    is_admin = is_authenticated and bool(getattr(user, "is_superuser", False))

    allowed = [HelpArticle.VISIBILITY_PUBLIC]
    if is_authenticated:
        allowed.append(HelpArticle.VISIBILITY_AUTHENTICATED)
    if is_staff:
        allowed.append(HelpArticle.VISIBILITY_STAFF)
    if is_admin:
        allowed.append(HelpArticle.VISIBILITY_ADMIN)

    return Q(visibility__in=allowed)


def _serialize_article(article):
    return {
        "id": article.pk,
        "slug": article.slug,
        "title": article.title,
        "summary": article.summary,
        "content": article.content,
        "module": article.module,
        "article_type": article.article_type,
        "visibility": article.visibility,
        "state": article.state,
        "route_path": article.route_path,
        "published": article.published,
    }


def _serialize_playbook(playbook):
    return {
        "id": playbook.pk,
        "slug": playbook.slug,
        "title": playbook.title,
        "summary": playbook.summary,
        "module": playbook.module,
    }


def _solomon_consumption_enabled() -> bool:
    return bool(
        getattr(settings, "CROWN_SOLOMON_API_ENABLED", False)
        and getattr(settings, "CROWN_SOLOMON_CONTEXT_ENABLED", False)
    )


def _normalized_context_payload(payload_dict: dict[str, Any]) -> dict[str, Any] | None:
    status = payload_dict.get("status")
    if status not in SOLOMON_CONTEXT_ALLOWED_STATUSES:
        return None

    resources = payload_dict.get("resources", [])
    playbooks = payload_dict.get("playbooks", [])
    context_rules = payload_dict.get("context_rules", [])

    if not isinstance(resources, list) or not isinstance(playbooks, list) or not isinstance(context_rules, list):
        return None

    return {
        "status": status,
        "resources": resources,
        "playbooks": playbooks,
        "context_rules": context_rules,
    }


def get_parent_enrollment_guidance(request):
    """Return optional parent enrollment guidance payload or None (silent noop)."""
    if not _solomon_consumption_enabled():
        return None

    try:
        adapter = OnboardingAdapter()
        payload = adapter.get_context(
            SolomonContextRequest(
                module="onboarding",
                route="/students/enrollment",
                audience="parent",
                scope="school",
                request=request,
            )
        )
    except Exception:
        return None

    if hasattr(payload, "to_dict"):
        payload_dict = payload.to_dict()
    elif isinstance(payload, dict):
        payload_dict = payload
    else:
        return None

    normalized = _normalized_context_payload(payload_dict)
    if not normalized:
        return None

    # Silent noop behavior for disabled state.
    if normalized["status"] == "disabled":
        return None

    return normalized


def get_contextual_solomon_help(
    request,
    slug="",
    route_path="",
    module="",
    audience="",
    context_key="",
):
    """Return contextual help for the given slug or route_path."""
    _ = (audience, context_key)
    primary_article = None
    related_articles = []
    playbooks = []

    qs = HELP_ARTICLE_MANAGER.filter(state=HelpArticle.STATE_PUBLISHED).filter(_visibility_qs(request))

    resolved_article = None

    if slug:
        resolved_article = qs.filter(slug=slug).first()

    if route_path and not resolved_article:
        resolved_article = qs.filter(route_path=route_path).first()

    if resolved_article:
        primary_article = _serialize_article(resolved_article)

    if module:
        exclude_pk = resolved_article.pk if resolved_article else None
        related_qs = qs.filter(module=module)
        if exclude_pk is not None:
            related_qs = related_qs.exclude(pk=exclude_pk)
        related_articles = [_serialize_article(a) for a in related_qs[:5]]

        pb_qs = SOLOMON_PLAYBOOK_MANAGER.filter(module=module)[:3]
        playbooks = [_serialize_playbook(p) for p in pb_qs]

    return {
        "primary_article": primary_article,
        "related_articles": related_articles,
        "playbooks": playbooks,
    }


def search_solomon_content(request, query="", module="", audience=""):
    """Search Solomon articles by query, module, and/or audience."""
    qs = HELP_ARTICLE_MANAGER.filter(state=HelpArticle.STATE_PUBLISHED).filter(_visibility_qs(request))

    if module:
        qs = qs.filter(module=module)

    if audience:
        qs = qs.filter(audiences__slug=audience)

    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(content__icontains=query))

    distinct_qs = qs.distinct()
    articles = [_serialize_article(a) for a in distinct_qs[:20]]
    categories = list(
        distinct_qs.exclude(article_type="")
        .values_list("article_type", flat=True)
        .distinct()
    )

    playbook_qs = SOLOMON_PLAYBOOK_MANAGER.all()
    if module:
        playbook_qs = playbook_qs.filter(module=module)
    if query:
        playbook_qs = playbook_qs.filter(
            Q(title__icontains=query) | Q(summary__icontains=query)
        )
    playbooks = [_serialize_playbook(p) for p in playbook_qs[:20]]

    return {
        "results": articles,
        "count": len(articles),
        "query": query,
        "module": module,
        "audience": audience,
        "categories": categories,
        "playbooks": playbooks,
    }
