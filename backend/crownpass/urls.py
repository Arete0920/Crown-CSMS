from django.urls import path

from .api import my_ticket_credential, my_tickets, redeem_credential

urlpatterns = [
    path("my-tickets/", my_tickets, name="my-tickets"),
    path(
        "my-tickets/<uuid:ticket_id>/credential/",
        my_ticket_credential,
        name="my-ticket-credential",
    ),
    path("redeem/", redeem_credential, name="redeem"),
]
