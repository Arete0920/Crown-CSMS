from django.urls import path
from . import api

urlpatterns = [
    # Board-level read-only (governance)
    path("board/compass/",      api.board_compass_summary, name="board_compass_summary"),
    path("board/risk-counts/",  api.board_risk_counts,    name="board_risk_counts"),

    # Staff: per-student signal detail
    path("students/<int:student_id>/signals/", api.student_signals, name="student_signals"),

    # Staff: intervention queue
    path("interventions/cases/",                        api.intervention_cases,   name="intervention_cases"),
    path("interventions/cases/<int:case_id>/actions/",  api.intervention_actions, name="intervention_actions"),
]
