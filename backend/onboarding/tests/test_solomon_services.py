"""
backend/onboarding/tests/test_solomon_services.py

Focused regression tests for Solomon service layer and API endpoints.

Covers:
  get_contextual_solomon_help():
    - slug resolution → primary_article returned
    - route_path resolution (slug empty/missing) → primary_article returned
    - slug takes precedence over route_path
    - draft / archived articles excluded by state filter
    - related articles exclude the primary article by pk (not slug) —
      i.e. the fix where exclude(slug="") would silently reinclude the primary
    - related articles are limited to 5
    - related articles respect module filter
    - playbooks returned by module
    - no module → empty related_articles and playbooks
    - audience / context_key params accepted without error
    - return dict has exactly the right top-level keys

  search_solomon_content():
    - response shape: all expected keys present
    - query filter matches on title
    - query filter matches on content
    - module filter narrows results
    - audience M2M filter narrows results
    - draft articles excluded
    - archived articles excluded
    - categories key populated from article_type values
    - playbooks key present and populated
    - playbook module filter
    - playbook query filter (title)
    - count == len(results)

  Solomon API endpoints (AllowAny — no credentials needed):
    - GET /api/v1/solomon/context/?slug=  → 200, correct keys
    - GET /api/v1/solomon/context/?route_path=  → 200
    - GET /api/v1/solomon/context/ (no match) → 404
    - related_articles in context response do not include the primary article
    - GET /api/v1/solomon/search/  → 200, correct keys
    - query param narrows search results
    - GET /api/v1/solomon/categories/  → 200, categories key present
    - categories populated from article_type
    - GET /api/v1/solomon/playbooks/  → 200, playbooks key present
    - module param narrows playbook results
"""
import pytest
from rest_framework.test import APIClient

from onboarding.models_tasks import (
    HelpArticle,
    SolomonAudience,
    SolomonPlaybook,
)
from onboarding.solomon_services import (
    get_contextual_solomon_help,
    search_solomon_content,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _article(
    slug,
    *,
    title="Help Title",
    module="fin",
    state=HelpArticle.STATE_PUBLISHED,
    visibility=HelpArticle.VISIBILITY_PUBLIC,
    route_path="",
    article_type=HelpArticle.TYPE_GUIDE,
    content="article body text",
):
    return HelpArticle.objects.create(
        slug=slug,
        title=title,
        module=module,
        state=state,
        visibility=visibility,
        route_path=route_path,
        article_type=article_type,
        content=content,
    )


def _playbook(slug, *, module="fin", title=None,
              state=HelpArticle.STATE_PUBLISHED,
              visibility=HelpArticle.VISIBILITY_PUBLIC, summary=""):
    return SolomonPlaybook.objects.create(
        slug=slug,
        title=title or f"PB {slug}",
        module=module,
        state=state,
        visibility=visibility,
        summary=summary,
    )


class _FakeRequest:
    """Minimal stand-in for DRF request used when calling service functions directly."""
    user = type("anon", (), {"is_authenticated": False, "is_staff": False})()


# ---------------------------------------------------------------------------
# get_contextual_solomon_help — unit tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGetContextualSolomonHelp:

    def test_resolve_by_slug_returns_primary(self):
        art = _article("fin-intro")
        payload = get_contextual_solomon_help(_FakeRequest(), slug="fin-intro")
        assert payload["primary_article"] is not None
        assert payload["primary_article"]["slug"] == "fin-intro"
        assert payload["primary_article"]["id"] == art.pk

    def test_resolve_by_route_path_when_slug_empty(self):
        art = _article("fin-route", route_path="/finance/overview")
        payload = get_contextual_solomon_help(
            _FakeRequest(), slug="", route_path="/finance/overview"
        )
        assert payload["primary_article"] is not None
        assert payload["primary_article"]["id"] == art.pk

    def test_resolve_by_route_path_when_slug_has_no_match(self):
        art = _article("rp-only", route_path="/dashboard/tuition")
        payload = get_contextual_solomon_help(
            _FakeRequest(), slug="nonexistent", route_path="/dashboard/tuition"
        )
        # slug doesn't match anything → falls through to route_path
        assert payload["primary_article"] is not None
        assert payload["primary_article"]["id"] == art.pk

    def test_slug_takes_precedence_over_route_path(self):
        by_slug = _article("slug-winner", route_path="")
        by_path = _article("path-only", route_path="/some/path")
        payload = get_contextual_solomon_help(
            _FakeRequest(), slug="slug-winner", route_path="/some/path"
        )
        assert payload["primary_article"]["id"] == by_slug.pk

    def test_no_match_returns_none_primary(self):
        payload = get_contextual_solomon_help(_FakeRequest(), slug="does-not-exist")
        assert payload["primary_article"] is None

    def test_draft_article_not_returned(self):
        _article("draft-ctxh", state=HelpArticle.STATE_DRAFT)
        payload = get_contextual_solomon_help(_FakeRequest(), slug="draft-ctxh")
        assert payload["primary_article"] is None

    def test_archived_article_not_returned(self):
        _article("archived-ctxh", state=HelpArticle.STATE_ARCHIVED)
        payload = get_contextual_solomon_help(_FakeRequest(), slug="archived-ctxh")
        assert payload["primary_article"] is None

    def test_related_excludes_primary_resolved_by_slug(self):
        """Core bug fix: primary resolved via slug must not reappear in related_articles."""
        primary = _article("primary-slug", module="fin")
        _article("related-one", module="fin")
        _article("related-two", module="fin")
        payload = get_contextual_solomon_help(
            _FakeRequest(), slug="primary-slug", module="fin"
        )
        assert payload["primary_article"]["id"] == primary.pk
        related_ids = [a["id"] for a in payload["related_articles"]]
        assert primary.pk not in related_ids

    def test_related_excludes_primary_resolved_by_route_path(self):
        """Core bug fix: primary resolved via route_path (slug='') must not reappear.

        Previously exclude(slug='') matched nothing, so the primary reappeared.
        The fix uses exclude(pk=resolved_article.pk) instead.
        """
        primary = _article("rp-primary", module="fin", route_path="/fin/main")
        _article("rp-related", module="fin")
        payload = get_contextual_solomon_help(
            _FakeRequest(), slug="", route_path="/fin/main", module="fin"
        )
        assert payload["primary_article"]["id"] == primary.pk
        related_ids = [a["id"] for a in payload["related_articles"]]
        assert primary.pk not in related_ids

    def test_related_limited_to_five(self):
        primary = _article("hub-art", module="m-hub")
        for i in range(7):
            _article(f"hub-rel-{i}", module="m-hub")
        payload = get_contextual_solomon_help(
            _FakeRequest(), slug="hub-art", module="m-hub"
        )
        assert len(payload["related_articles"]) <= 5

    def test_related_filtered_by_module(self):
        _article("mod-a-1", module="mod-a")
        _article("mod-b-1", module="mod-b")
        payload = get_contextual_solomon_help(
            _FakeRequest(), slug="mod-a-1", module="mod-a"
        )
        for rel in payload["related_articles"]:
            assert rel["module"] == "mod-a"

    def test_playbooks_returned_for_module(self):
        _article("art-with-pb", module="finmod")
        _playbook("pb-finmod-1", module="finmod")
        _playbook("pb-finmod-2", module="finmod")
        payload = get_contextual_solomon_help(
            _FakeRequest(), slug="art-with-pb", module="finmod"
        )
        assert len(payload["playbooks"]) == 2

    def test_no_module_returns_empty_related_and_playbooks(self):
        _article("standalone-art", module="fin")
        payload = get_contextual_solomon_help(
            _FakeRequest(), slug="standalone-art", module=""
        )
        assert payload["related_articles"] == []
        assert payload["playbooks"] == []

    def test_audience_and_context_key_accepted_without_error(self):
        """audience/context_key params are accepted; they must not raise."""
        _article("ctx-art", module="fin")
        payload = get_contextual_solomon_help(
            _FakeRequest(),
            slug="ctx-art",
            module="fin",
            audience="parent",
            context_key="dashboard.overview",
        )
        assert "primary_article" in payload

    def test_return_shape_has_exactly_three_keys(self):
        _article("shape-art", module="fin")
        payload = get_contextual_solomon_help(
            _FakeRequest(), slug="shape-art", module="fin"
        )
        assert set(payload.keys()) == {"primary_article", "related_articles", "playbooks"}

    def test_primary_article_has_expected_fields(self):
        _article("fields-art", module="fin")
        payload = get_contextual_solomon_help(_FakeRequest(), slug="fields-art")
        art = payload["primary_article"]
        for field in ("id", "slug", "title", "summary", "content", "module",
                      "article_type", "visibility", "state", "route_path", "published"):
            assert field in art, f"missing field: {field}"


# ---------------------------------------------------------------------------
# search_solomon_content — unit tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSearchSolomonContent:

    def test_response_shape_keys_present(self):
        payload = search_solomon_content(_FakeRequest())
        for key in ("results", "count", "query", "module", "audience",
                    "categories", "playbooks"):
            assert key in payload, f"missing key: {key}"

    def test_count_matches_results_length(self):
        _article("cnt-a", module="cnt")
        _article("cnt-b", module="cnt")
        payload = search_solomon_content(_FakeRequest(), module="cnt")
        assert payload["count"] == len(payload["results"])

    def test_query_filters_by_title(self):
        _article("title-match", title="Finance Budget Guide")
        _article("title-no-match", title="Admissions Overview")
        payload = search_solomon_content(_FakeRequest(), query="Finance Budget")
        slugs = [r["slug"] for r in payload["results"]]
        assert "title-match" in slugs
        assert "title-no-match" not in slugs

    def test_query_filters_by_content(self):
        _article("content-match", content="unique tuition calculation formula")
        _article("content-no-match", content="something entirely unrelated")
        payload = search_solomon_content(
            _FakeRequest(), query="unique tuition calculation"
        )
        slugs = [r["slug"] for r in payload["results"]]
        assert "content-match" in slugs
        assert "content-no-match" not in slugs

    def test_module_filter_narrows_results(self):
        _article("fin-search-art", module="finance-search")
        _article("adm-search-art", module="admissions-search")
        payload = search_solomon_content(_FakeRequest(), module="finance-search")
        slugs = [r["slug"] for r in payload["results"]]
        assert "fin-search-art" in slugs
        assert "adm-search-art" not in slugs

    def test_audience_filter_narrows_results(self):
        audience = SolomonAudience.objects.create(slug="parent-aud", name="Parent")
        targeted = _article("parent-targeted", module="fin")
        targeted.audiences.add(audience)
        _article("not-targeted", module="fin")
        payload = search_solomon_content(_FakeRequest(), audience="parent-aud")
        slugs = [r["slug"] for r in payload["results"]]
        assert "parent-targeted" in slugs
        assert "not-targeted" not in slugs

    def test_draft_articles_excluded(self):
        _article("draft-search", state=HelpArticle.STATE_DRAFT)
        payload = search_solomon_content(_FakeRequest())
        slugs = [r["slug"] for r in payload["results"]]
        assert "draft-search" not in slugs

    def test_archived_articles_excluded(self):
        _article("archived-search", state=HelpArticle.STATE_ARCHIVED)
        payload = search_solomon_content(_FakeRequest())
        slugs = [r["slug"] for r in payload["results"]]
        assert "archived-search" not in slugs

    def test_categories_populated_from_article_type(self):
        _article("cat-guide-art", article_type=HelpArticle.TYPE_GUIDE)
        _article("cat-faq-art", article_type=HelpArticle.TYPE_FAQ)
        payload = search_solomon_content(_FakeRequest())
        assert HelpArticle.TYPE_GUIDE in payload["categories"]
        assert HelpArticle.TYPE_FAQ in payload["categories"]

    def test_categories_never_contains_empty_string(self):
        """The service excludes blank article_type values from categories."""
        _article("blank-type-art", article_type=HelpArticle.TYPE_GUIDE)
        payload = search_solomon_content(_FakeRequest())
        assert "" not in payload["categories"]

    def test_playbooks_key_populated(self):
        _playbook("pb-search-1", module="fin")
        payload = search_solomon_content(_FakeRequest())
        pb_slugs = [p["slug"] for p in payload["playbooks"]]
        assert "pb-search-1" in pb_slugs

    def test_playbooks_module_filter(self):
        _playbook("pb-finance-mod", module="finance-mod")
        _playbook("pb-other-mod", module="other-mod")
        payload = search_solomon_content(_FakeRequest(), module="finance-mod")
        pb_slugs = [p["slug"] for p in payload["playbooks"]]
        assert "pb-finance-mod" in pb_slugs
        assert "pb-other-mod" not in pb_slugs

    def test_playbooks_query_filter_on_title(self):
        _playbook("pb-budget-q", module="fin", title="Budget Planning Playbook")
        _playbook("pb-other-q", module="fin", title="Generic Playbook")
        payload = search_solomon_content(_FakeRequest(), query="Budget Planning")
        pb_slugs = [p["slug"] for p in payload["playbooks"]]
        assert "pb-budget-q" in pb_slugs
        assert "pb-other-q" not in pb_slugs

    def test_playbook_serializer_shape(self):
        _playbook("pb-shape", module="fin")
        payload = search_solomon_content(_FakeRequest())
        match = next((p for p in payload["playbooks"] if p["slug"] == "pb-shape"), None)
        assert match is not None, "Playbook pb-shape not found in search results"
        for field in ("id", "slug", "title", "summary", "module"):
            assert field in match, f"missing playbook field: {field}"

    def test_article_serializer_shape(self):
        _article("shape-search-art", module="fin")
        payload = search_solomon_content(_FakeRequest(), module="fin")
        match = next((r for r in payload["results"] if r["slug"] == "shape-search-art"), None)
        assert match is not None, "Article shape-search-art not found in search results"
        for field in ("id", "slug", "title", "summary", "content", "module",
                      "article_type", "visibility", "state", "route_path", "published"):
            assert field in match, f"missing article field: {field}"


# ---------------------------------------------------------------------------
# Solomon API endpoint tests
# ---------------------------------------------------------------------------

SOLOMON_CONTEXT = "/api/v1/solomon/context/"
SOLOMON_SEARCH = "/api/v1/solomon/search/"
SOLOMON_CATEGORIES = "/api/v1/solomon/categories/"
SOLOMON_PLAYBOOKS = "/api/v1/solomon/playbooks/"


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.mark.django_db
class TestSolomonContextEndpoint:

    def test_slug_match_returns_200_with_shape(self, anon_client):
        _article("ep-intro", module="fin")
        res = anon_client.get(SOLOMON_CONTEXT, {"slug": "ep-intro", "module": "fin"})
        assert res.status_code == 200
        data = res.json()
        assert data["primary_article"]["slug"] == "ep-intro"
        assert "related_articles" in data
        assert "playbooks" in data

    def test_route_path_match_returns_200(self, anon_client):
        _article("ep-route-art", module="fin", route_path="/finance/tuition")
        res = anon_client.get(
            SOLOMON_CONTEXT, {"route_path": "/finance/tuition", "module": "fin"}
        )
        assert res.status_code == 200
        assert res.json()["primary_article"]["slug"] == "ep-route-art"

    def test_no_match_returns_404(self, anon_client):
        res = anon_client.get(SOLOMON_CONTEXT, {"slug": "ep-does-not-exist"})
        assert res.status_code == 404

    def test_related_articles_do_not_include_primary(self, anon_client):
        """Regression: primary resolved by slug must not reappear in related_articles."""
        primary = _article("ep-excl-primary", module="ep-excl-mod")
        _article("ep-excl-secondary", module="ep-excl-mod")
        res = anon_client.get(
            SOLOMON_CONTEXT, {"slug": "ep-excl-primary", "module": "ep-excl-mod"}
        )
        assert res.status_code == 200
        related_ids = [a["id"] for a in res.json()["related_articles"]]
        assert primary.pk not in related_ids

    def test_route_path_related_articles_do_not_include_primary(self, anon_client):
        """Regression: primary resolved by route_path must not reappear in related_articles."""
        primary = _article(
            "ep-rp-excl-primary", module="ep-rp-mod", route_path="/rp-excl/main"
        )
        _article("ep-rp-excl-secondary", module="ep-rp-mod")
        res = anon_client.get(
            SOLOMON_CONTEXT,
            {"slug": "", "route_path": "/rp-excl/main", "module": "ep-rp-mod"},
        )
        assert res.status_code == 200
        related_ids = [a["id"] for a in res.json()["related_articles"]]
        assert primary.pk not in related_ids


@pytest.mark.django_db
class TestSolomonSearchEndpoint:

    def test_returns_200_with_correct_keys(self, anon_client):
        res = anon_client.get(SOLOMON_SEARCH)
        assert res.status_code == 200
        for key in ("results", "count", "categories", "playbooks"):
            assert key in res.json(), f"missing key: {key}"

    def test_query_param_filters_results(self, anon_client):
        _article("ep-search-match", title="Tuition Calculator Help")
        _article("ep-search-other", title="Admissions FAQ Overview")
        res = anon_client.get(SOLOMON_SEARCH, {"q": "Tuition Calculator"})
        assert res.status_code == 200
        slugs = [r["slug"] for r in res.json()["results"]]
        assert "ep-search-match" in slugs
        assert "ep-search-other" not in slugs

    def test_module_param_filters_results(self, anon_client):
        _article("ep-search-fin", module="ep-fin-mod")
        _article("ep-search-adm", module="ep-adm-mod")
        res = anon_client.get(SOLOMON_SEARCH, {"module": "ep-fin-mod"})
        slugs = [r["slug"] for r in res.json()["results"]]
        assert "ep-search-fin" in slugs
        assert "ep-search-adm" not in slugs


@pytest.mark.django_db
class TestSolomonCategoriesEndpoint:

    def test_returns_200_with_categories_key(self, anon_client):
        res = anon_client.get(SOLOMON_CATEGORIES)
        assert res.status_code == 200
        assert "categories" in res.json()

    def test_categories_populated_from_article_types(self, anon_client):
        _article("ep-cat-faq", article_type=HelpArticle.TYPE_FAQ)
        res = anon_client.get(SOLOMON_CATEGORIES)
        assert HelpArticle.TYPE_FAQ in res.json()["categories"]


@pytest.mark.django_db
class TestSolomonPlaybooksEndpoint:

    def test_returns_200_with_playbooks_key(self, anon_client):
        res = anon_client.get(SOLOMON_PLAYBOOKS)
        assert res.status_code == 200
        assert "playbooks" in res.json()

    def test_module_param_filters_playbooks(self, anon_client):
        _playbook("ep-pb-finance", module="ep-pb-fin")
        _playbook("ep-pb-hr", module="ep-pb-hr")
        res = anon_client.get(SOLOMON_PLAYBOOKS, {"module": "ep-pb-fin"})
        pb_slugs = [p["slug"] for p in res.json()["playbooks"]]
        assert "ep-pb-finance" in pb_slugs
        assert "ep-pb-hr" not in pb_slugs

    def test_query_param_filters_playbooks(self, anon_client):
        _playbook("ep-pb-budget", module="fin", title="Budget Planning Playbook")
        _playbook("ep-pb-other", module="fin", title="Generic Playbook")
        res = anon_client.get(SOLOMON_PLAYBOOKS, {"q": "Budget Planning"})
        pb_slugs = [p["slug"] for p in res.json()["playbooks"]]
        assert "ep-pb-budget" in pb_slugs
        assert "ep-pb-other" not in pb_slugs
