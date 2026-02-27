"""
comms/outbox.py — backward-compat re-export.

OutboxMessage is now defined canonically in comms/models.py so that Django's
ORM, migrations, and admin all resolve it through the standard app label
`comms`.  This file exists only so that older import paths continue to work.
"""
from .models import OutboxMessage  # noqa: F401
