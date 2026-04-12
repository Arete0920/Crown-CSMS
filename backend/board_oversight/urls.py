from django.urls import path
from . import views

urlpatterns = [
    # Primary endpoint consumed by existing BoardDashboard frontend
    path("metrics/", views.board_metrics, name="board_oversight_metrics"),
    # Structured spec endpoints
    path("dashboard/", views.board_dashboard, name="board_oversight_dashboard"),
    path("snapshots/", views.list_snapshots, name="board_oversight_snapshots"),
    path("packets/", views.list_packets, name="board_oversight_packets"),
    path("packets/<int:packet_id>/", views.get_packet, name="board_oversight_packet_detail"),
]
