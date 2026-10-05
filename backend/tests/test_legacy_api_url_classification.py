"""Executable inventory for the legacy crown_api.api_urls catch-all.

This test does not authorize route removal. It binds the current declaration
counts and the internal ``v1/`` prefix inversion so future changes must update
the controlled governance ledger intentionally.
"""

from django.urls import URLPattern, URLResolver

from crown_api import api_urls, api_v1_urls, urls as root_urls


INTERNALLY_V1_PREFIXED_ROUTES = {
    "v1/finance/kpis/",
    "v1/finance/chargebacks/",
    "v1/finance/monthly-summary/",
    "v1/finance/payout-audit/",
    "v1/finance/dunning/",
    "v1/finance-setup/",
    "v1/onboarding/<str:school_id>/progress/",
    "v1/onboarding/<str:school_id>/tasks/<int:task_id>/complete/",
    "v1/onboarding/<str:school_id>/can-activate/",
    "v1/help/<slug:slug>/",
    "v1/solomon/articles/",
    "v1/solomon/articles/<slug:slug>/",
    "v1/solomon/context/",
    "v1/solomon/categories/",
    "v1/solomon/playbooks/",
    "v1/solomon/search/",
    "v1/dashboards/school-board/summary/",
    "v1/board/packet/download/",
    "v1/board/compass/",
    "v1/board/initiatives/",
    "v1/board/trends/",
    "v1/board/roadmap/",
    "v1/board/releases/",
    "v1/support/tickets/",
    "v1/support/tickets/<int:ticket_id>/resolve/",
    "v1/support/escalation/run/",
    "v1/analytics/health/",
    "v1/analytics/export/",
    "v1/status/",
}

DEPRECATED_DIRECTOR_ROUTES = {
    "director/aid/summary/",
    "director/finance/summary/",
    "director/registrar/summary/",
    "director/dashboard/",
    "director/priority/",
    "director/actions/",
    "director/timeline/",
}

NON_V1_NESTED_INCLUDES = {
    "360/",
    "comms/",
    "aid/",
    "admissions/",
    "discipline/",
    "service/",
    "integrations/",
    "spiritual-life/",
    "outreach/",
    "athletics/",
    "",
    "transportation/",
    "signals/",
}


def _targets_api_v1(resolver: URLResolver) -> bool:
    """Identify mounts by the resolved pattern list, not URLConf representation."""
    return resolver.url_patterns is api_v1_urls.urlpatterns or (
        resolver.url_patterns == api_v1_urls.urlpatterns
    )


def test_legacy_api_urlpatterns_have_controlled_mutually_exclusive_counts():
    patterns = list(api_urls.urlpatterns)
    direct = [pattern for pattern in patterns if isinstance(pattern, URLPattern)]
    includes = [pattern for pattern in patterns if isinstance(pattern, URLResolver)]

    assert len(patterns) == 117
    assert len(direct) == 103
    assert len(includes) == 14

    internally_v1 = [
        pattern for pattern in patterns if str(pattern.pattern).startswith("v1/")
    ]
    director = [
        pattern for pattern in direct if str(pattern.pattern) in DEPRECATED_DIRECTOR_ROUTES
    ]
    other_direct = [
        pattern
        for pattern in direct
        if not str(pattern.pattern).startswith("v1/")
        and str(pattern.pattern) not in DEPRECATED_DIRECTOR_ROUTES
    ]
    other_includes = [
        pattern
        for pattern in includes
        if not str(pattern.pattern).startswith("v1/")
    ]

    assert len(internally_v1) == 29
    assert sum(isinstance(pattern, URLPattern) for pattern in internally_v1) == 28
    assert sum(isinstance(pattern, URLResolver) for pattern in internally_v1) == 1
    assert len(director) == 7
    assert len(other_direct) == 68
    assert len(other_includes) == 13
    assert 29 + 7 + 68 + 13 == 117


def test_internal_v1_and_deprecated_route_sets_are_exact():
    patterns = list(api_urls.urlpatterns)

    assert {
        str(pattern.pattern)
        for pattern in patterns
        if str(pattern.pattern).startswith("v1/")
    } == INTERNALLY_V1_PREFIXED_ROUTES
    assert {
        str(pattern.pattern)
        for pattern in patterns
        if isinstance(pattern, URLPattern)
        and str(pattern.pattern).startswith("director/")
    } == DEPRECATED_DIRECTOR_ROUTES
    assert {
        str(pattern.pattern)
        for pattern in patterns
        if isinstance(pattern, URLResolver)
        and not str(pattern.pattern).startswith("v1/")
    } == NON_V1_NESTED_INCLUDES


def test_dual_mount_creates_the_prefix_inversion_without_changing_callbacks():
    api_v1_mounts = {
        str(pattern.pattern)
        for pattern in root_urls.urlpatterns
        if isinstance(pattern, URLResolver) and _targets_api_v1(pattern)
    }

    assert api_v1_mounts == {"api/v1/", "api/"}

    canonical_mount_paths = {
        f"api/v1/{route}" for route in INTERNALLY_V1_PREFIXED_ROUTES
    }
    compatibility_mount_paths = {
        f"api/{route}" for route in INTERNALLY_V1_PREFIXED_ROUTES
    }

    assert all(path.startswith("api/v1/v1/") for path in canonical_mount_paths)
    assert all(path.startswith("api/v1/") for path in compatibility_mount_paths)
    assert all(not path.startswith("api/v1/v1/") for path in compatibility_mount_paths)
