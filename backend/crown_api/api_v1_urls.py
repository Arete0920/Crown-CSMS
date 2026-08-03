"""
Canonical API v1 routes.
All /api/v1/* and /api/* routes resolve through here.
"""
from importlib.util import find_spec

from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from applications.views_admissions import (
    admissions_drilldown,
    admissions_submit,
    admissions_public_config,
    admissions_enrollment_state,
    admissions_enrollment_state_update,
    admissions_contract_detail,
    admissions_contract_update,
    admissions_contract_amend,
    admissions_lifecycle_chain_update,
    admissions_application_event_replay,
)
from crown_api.admissions_runtime import admissions_summary
from crown_api.system_views import SeedStatusView, demo_reset_view, diagnose_db_tables_view, fix_schema_drift_view
from crown_api.ops_views import ensure_ci_user, demo_school
from crown_api.release_gate_views import (
    ExportsIndexView,
    ReportsExportFacadeView,
    TranscriptGenerateProbeView,
    TranscriptRouteProbeView,
)


def _optional_module_exists(module_path: str) -> bool:
    try:
        return find_spec(module_path) is not None
    except (ModuleNotFoundError, ValueError):
        return False


urlpatterns = [
    # DEV-only ops endpoints (must come early before includes)
    path("system/ensure-ci-user/", ensure_ci_user, name="system-ensure-ci-user"),
    path("system/demo-school/", demo_school, name="system-demo-school"),

    # Authentication
    path("sandbox/", include("sandbox_demo.urls")),
    path("auth/token/", TokenObtainPairView.as_view(), name="v1_token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="v1_token_refresh"),

    # Admissions funnel (frozen contract)
    path("admissions/public-config/", admissions_public_config, name="admissions_public_config"),
    path("admissions/summary/", admissions_summary, name="admissions_summary"),
    path("admissions/drilldown/", admissions_drilldown, name="admissions_drilldown"),
    path("admissions/submit/", admissions_submit, name="admissions_submit"),
    path(
        "admissions/applications/<uuid:application_id>/enrollment-state/",
        admissions_enrollment_state,
        name="admissions_enrollment_state",
    ),
    path(
        "admissions/applications/<uuid:application_id>/enrollment-state/update/",
        admissions_enrollment_state_update,
        name="admissions_enrollment_state_update",
    ),
    path(
        "admissions/applications/<uuid:application_id>/contract/",
        admissions_contract_detail,
        name="admissions_contract_detail",
    ),
    path(
        "admissions/applications/<uuid:application_id>/contract/update/",
        admissions_contract_update,
        name="admissions_contract_update",
    ),
    path(
        "admissions/applications/<uuid:application_id>/contract/amend/",
        admissions_contract_amend,
        name="admissions_contract_amend",
    ),
    path(
        "admissions/applications/<uuid:application_id>/lifecycle-chain/update/",
        admissions_lifecycle_chain_update,
        name="admissions_lifecycle_chain_update",
    ),
    path(
        "admissions/applications/<uuid:application_id>/event-replay/",
        admissions_application_event_replay,
        name="admissions_application_event_replay",
    ),
    path("learning-continuity/", include("learning_continuity.urls")),
    # System telemetry
    path("system/seed-status/", SeedStatusView.as_view(), name="seed_status"),
    path("system/demo-reset/", demo_reset_view, name="system-demo-reset"),
    path("system/diagnose-db-tables/", diagnose_db_tables_view, name="system-diagnose-db-tables"),
    path("system/fix-schema-drift/", fix_schema_drift_view, name="system-fix-schema-drift"),

    # Release-certification compatibility probes (non-404 explicit surfaces)
    path("transcripts/", TranscriptRouteProbeView.as_view(), name="transcripts-probe"),
    path("transcripts/generate/", TranscriptGenerateProbeView.as_view(), name="transcripts-generate-probe"),
    path("exports/", ExportsIndexView.as_view(), name="exports-index"),
    path("reports/export/", ReportsExportFacadeView.as_view(), name="reports-export-facade"),

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
    # Aftercare / Daycare / Extended Care
    path("aftercare/", include("aftercare.urls")),
    # Summer Camp
    path("summer-camp/", include("summer_camp.urls")),

    # Home Academy / Homeschool Affiliation
    path("home-academy/", include("home_academy.urls")),

    # M365 readiness/status routes (governance.urls at m365/ prefix)
    path("m365/", include("governance.urls")),

    # Legacy api_urls catch-all (must come AFTER specific module includes above)
    path("", include("crown_api.api_urls")),
]

if _optional_module_exists("crm_marketing.api.urls"):
    # CRM Marketing add-on (non-canonical core truth)
    urlpatterns.insert(-4, path("crm/", include("crm_marketing.api.urls")))
