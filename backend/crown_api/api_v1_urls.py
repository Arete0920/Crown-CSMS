"""
Canonical API v1 routes.
All /api/v1/* and /api/* routes resolve through here.
"""
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from applications.views_admissions import admissions_summary, admissions_drilldown
from crown_api.system_views import SeedStatusView, demo_reset_view, diagnose_db_tables_view, fix_schema_drift_view
from crown_api.ops_views import ensure_ci_user, demo_school

urlpatterns = [
    # DEV-only ops endpoints (must come early before includes)
    path("system/ensure-ci-user/", ensure_ci_user, name="system-ensure-ci-user"),
    path("system/demo-school/", demo_school, name="system-demo-school"),

    # Authentication
    path("auth/token/", TokenObtainPairView.as_view(), name="v1_token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="v1_token_refresh"),

    # Admissions funnel (frozen contract)
    path("admissions/summary/", admissions_summary, name="admissions_summary"),
    path("admissions/drilldown/", admissions_drilldown, name="admissions_drilldown"),
    # System telemetry
    path("system/seed-status/", SeedStatusView.as_view(), name="seed_status"),
    path("system/demo-reset/", demo_reset_view, name="system-demo-reset"),
    path("system/diagnose-db-tables/", diagnose_db_tables_view, name="system-diagnose-db-tables"),
    path("system/fix-schema-drift/", fix_schema_drift_view, name="system-fix-schema-drift"),

    # Keep the same effective ordering you already rely on.
    # If any patterns collide, earlier includes win.
    path("academics-ro/", include("academics_ro.urls")),
    path("", include("academics.urls")),
    path("curricula/", include("curricula.urls")),
    path("", include("gradebook.urls")),
    path("", include("households.urls")),
    path("", include("crown_api.billing_api.urls")),
    path("", include("crown_api.exports.urls")),
    # Financial Aid endpoints
    path("financial-aid/", include("financial_aid.urls")),
    path("payments/", include("payments.api_urls")),
    # Sprint expansion modules — must come BEFORE crown_api.api_urls to avoid shadowing.
    # crown_api.api_urls registers legacy hardcoded metric stubs for these paths;
    # placing real includes first ensures Django first-match resolves to real views.
    path("board/", include("board_oversight.urls")),
    path("hr/", include("hr.urls")),
    path("advancement/", include("advancement.urls")),
    path("pd/", include("pdhub.urls")),
    path("safety/", include("safety.urls")),
    path("connectors/", include("integrations_real.urls")),
    path("student-records/", include("student_records.urls")),
    # Parent360 explicit v1 route
    path("parent360/", include("parent360.api.urls")),

    # Legacy api_urls catch-all (must come AFTER specific module includes above)
    path("", include("crown_api.api_urls")),
]

