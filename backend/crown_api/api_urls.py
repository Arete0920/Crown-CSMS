from django.urls import path
from crown_api.director_views import (
    aid_summary,
    finance_summary,
    registrar_summary,
    director_dashboard,
    director_priority,
    director_actions,
    director_timeline,
)

urlpatterns = [
    path("director/aid/summary/", aid_summary, name="aid_summary"),
    path("director/finance/summary/", finance_summary, name="finance_summary"),
    path("director/registrar/summary/", registrar_summary, name="registrar_summary"),
    path("director/dashboard/", director_dashboard, name="director_dashboard"),
    path("director/priority/", director_priority, name="director_priority"),
    path("director/actions/", director_actions, name="director_actions"),
    path("director/timeline/", director_timeline, name="director_timeline"),
]
