from django.urls import path

from crown_api.views_comms import thread_detail, threads_list


# Compatibility alias only. The former comms.api mutation endpoints were wired to
# an incompatible MessageThread/Message contract and included an authenticated-only
# arbitrary-recipient email smoke endpoint. Production traffic now uses the
# canonical tenant/household-scoped read authority; unsupported duplicate writes
# fail closed instead of pretending to succeed.
urlpatterns = [
    path("threads/", threads_list, name="comms_threads_list"),
    path("threads/<uuid:thread_id>/", thread_detail, name="comms_thread_detail"),
]
