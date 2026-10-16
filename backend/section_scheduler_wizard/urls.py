from django.urls import path
from section_scheduler_wizard import compass_api, planning_preview_api, standalone_api, views
from crown_api.views_scheduling import my_schedule

urlpatterns = [
    path("my-schedule/", my_schedule),
    path("preview/", planning_preview_api.preview),
    path("preview/options/", planning_preview_api.preview_options),
    path("compass/published/", compass_api.published_scheduling_metrics),
    path("standalone/import-preview/", standalone_api.standalone_import_preview),
    path("standalone/export-preview/", standalone_api.standalone_export_preview),
    path("", views.create_session),
    path("<uuid:session_id>/configure/", views.configure),
    path("<uuid:session_id>/options/", views.options),
    path("<uuid:session_id>/sections/", views.set_sections),
    path("<uuid:session_id>/commit/", views.commit),
    path("<uuid:session_id>/verify/", views.verify),
    path("<uuid:session_id>/undo/", views.undo_publication),
]
