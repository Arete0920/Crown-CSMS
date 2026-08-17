from django.urls import path

from crown_api.views_comms import threads_list, thread_detail
from comms.api.retired_views import retired_write

urlpatterns = [
    path("threads/", threads_list, name="comms_threads_list"),
    path("threads/<uuid:thread_id>/", thread_detail, name="comms_thread_detail"),
    path("threads/<uuid:thread_id>/messages/", retired_write, name="comms_thread_post_message"),
    path("compose/", retired_write, name="comms_compose"),
    path("send-test-email/", retired_write, name="comms_send_test_email"),
]
