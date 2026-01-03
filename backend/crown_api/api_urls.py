from importlib import import_module
from django.urls import path


def get_aid_summary(request):
    from crown_api.director_views import aid_summary
    return aid_summary(request)


def get_finance_summary(request):
    from crown_api.director_views import finance_summary
    return finance_summary(request)


def get_registrar_summary(request):
    from crown_api.director_views import registrar_summary
    return registrar_summary(request)


def get_director_dashboard(request):
    from crown_api.director_views import director_dashboard
    return director_dashboard(request)


def get_director_priority(request):
    from crown_api.director_views import director_priority
    return director_priority(request)


def post_director_actions(request):
    from crown_api.director_views import director_actions
    return director_actions(request)


def get_director_timeline(request):
    from crown_api.director_views import director_timeline
    return director_timeline(request)


urlpatterns = [
    path("director/aid/summary/", get_aid_summary, name="aid_summary"),
    path("director/finance/summary/", get_finance_summary, name="finance_summary"),
    path("director/registrar/summary/", get_registrar_summary, name="registrar_summary"),
    path("director/dashboard/", get_director_dashboard, name="director_dashboard"),
    path("director/priority/", get_director_priority, name="director_priority"),
    path("director/actions/", post_director_actions, name="director_actions"),
    path("director/timeline/", get_director_timeline, name="director_timeline"),
]
