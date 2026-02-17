from django.urls import path
from comms.api.views import ThreadsList, ThreadDetail, ThreadPostMessage, ComposeThread

urlpatterns = [
    path("threads/", ThreadsList.as_view(), name="comms_threads_list"),
    path("threads/<uuid:thread_id>/", ThreadDetail.as_view(), name="comms_thread_detail"),
    path("threads/<uuid:thread_id>/messages/", ThreadPostMessage.as_view(), name="comms_thread_post_message"),
    path("compose/", ComposeThread.as_view(), name="comms_compose"),
]
