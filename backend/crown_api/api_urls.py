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


urlpatterns = [
    path("director/aid/summary/", get_aid_summary, name="aid_summary"),
    path("director/finance/summary/", get_finance_summary, name="finance_summary"),
    path("director/registrar/summary/", get_registrar_summary, name="registrar_summary"),
]
