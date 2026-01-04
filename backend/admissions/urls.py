from django.urls import path
from . import views

app_name = 'admissions'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('applications/', views.applications_list, name='applications_list'),
    path('applications/<uuid:id>/', views.application_detail, name='application_detail'),
]
