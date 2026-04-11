"""
onboarding/solomon_services.py

Service layer for Solomon contextual help and content search.
"""
from onboarding.models_tasks import HelpArticle, SolomonPlaybook


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


def get_contextual_solomon_help(
    request,
    slug="",
    route_path="",
    module="",
    audience="",
    context_key="",
):
    """Return contextual help for the given slug or route_path."""
    primary_article = None
    related_articles = []
    playbooks = []

    qs = HelpArticle.objects.filter(state=HelpArticle.STATE_PUBLISHED)

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

        pb_qs = SolomonPlaybook.objects.filter(module=module)[:3]
        playbooks = [_serialize_playbook(p) for p in pb_qs]

    return {
        "primary_article": primary_article,
        "related_articles": related_articles,
        "playbooks": playbooks,
    }


def search_solomon_content(request, query="", module="", audience=""):
    """Search Solomon articles by query, module, and/or audience."""
    qs = HelpArticle.objects.filter(state=HelpArticle.STATE_PUBLISHED)

    if module:
        qs = qs.filter(module=module)

    if audience:
        qs = qs.filter(audiences__slug=audience)

    if query:
        from django.db.models import Q
        qs = qs.filter(Q(title__icontains=query) | Q(content__icontains=query))

    articles = [_serialize_article(a) for a in qs.distinct()[:20]]

    return {
        "results": articles,
        "count": len(articles),
        "query": query,
        "module": module,
        "audience": audience,
    }
