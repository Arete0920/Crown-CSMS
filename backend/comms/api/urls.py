from django.urls import path
from comms import release_api

from crown_api.views_comms import thread_detail, threads_list


# Compatibility alias only. The former comms.api mutation endpoints were wired to
# an incompatible MessageThread/Message contract and included an authenticated-only
# arbitrary-recipient email smoke endpoint. Production traffic now uses the
# canonical tenant/household-scoped read authority; unsupported duplicate writes
# fail closed instead of pretending to succeed.
urlpatterns = [
    path("releases/session/<uuid:session_id>/deadline/", release_api.session_deadline),
    path("releases/session/<uuid:session_id>/", release_api.releases),
    path("releases/<uuid:release_id>/<str:action>/", release_api.release_action),
    path("family-releases/", release_api.family_feed),
    path("family-releases/<uuid:release_id>/respond/", release_api.family_response),
    path("threads/", threads_list, name="comms_threads_list"),
    path("threads/<uuid:thread_id>/", thread_detail, name="comms_thread_detail"),
]
