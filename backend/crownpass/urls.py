from django.urls import path

from .api import my_tickets

app_name = "crownpass"

urlpatterns = [
    path("my-tickets/", my_tickets, name="my-tickets"),
]
