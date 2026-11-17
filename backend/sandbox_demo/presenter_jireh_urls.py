from django.urls import path
from . import presenter_jireh as api

urlpatterns = [
    path("aid/family/", api.aid_family),
    path("sgo/family/programs/", api.sgo_programs),
    path("sgo/family/submit/", api.sgo_submit),
    path("sgo/family/applications/<uuid:application_id>/", api.sgo_application),
    path("sgo/family/applications/<uuid:application_id>/correct/", api.sgo_correct),
    path("sgo/processor/programs/", api.sgo_processor_programs),
    path("sgo/processor/programs/<uuid:program_id>/queue/", api.sgo_queue),
    path("sgo/processor/applications/<uuid:application_id>/request-correction/", api.sgo_request_correction),
]
