"""Run the fictional Heritage demo with a larger *local-only* accept queue.

The standard Django development server has a ten-connection accept backlog.
Windows buyer rehearsals launch several dashboard API requests concurrently,
so a saturated backlog can yield refused Vite-proxy connections (HTTP 502)
even while other Django requests succeed. This command changes only the
local demo listener; it is not a production server or a deployment setting.
"""

from __future__ import annotations

import os

from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.commands.runserver import Command as RunserverCommand
from django.core.servers.basehttp import WSGIServer


class HeritageLocalWSGIServer(WSGIServer):
    """Keep local parallel dashboard requests in a bounded accept backlog."""

    request_queue_size = 128


class Command(RunserverCommand):
    """Reject hosted/non-demo execution before opening the local listener."""

    help = "Run the isolated local Heritage demo with a burst-safe accept queue."
    server_cls = HeritageLocalWSGIServer

    def handle(self, *args: object, **options: object) -> object:
        """Require an explicit local SQLite demo and loopback-only listener."""
        local_flags = (
            os.environ.get("CROWN_ENV") == "local"
            and os.environ.get("DJANGO_ENV") == "local"
            and os.environ.get("VITE_LOCAL_DEMO") == "1"
        )
        hosted = any(
            os.environ.get(key)
            for key in ("WEBSITE_HOSTNAME", "WEBSITE_INSTANCE_ID", "AZURE_ENVIRONMENT")
        )
        sqlite_engine = settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
        if (
            not local_flags
            or hosted
            or not settings.DEBUG
            or not sqlite_engine
            or options.get("addrport") != "127.0.0.1:8000"
            or options.get("use_reloader") is not False
        ):
            raise CommandError(
                "heritage_runserver requires the explicit local SQLite demo, "
                "127.0.0.1:8000 and --noreload; hosted execution is forbidden."
            )
        return super().handle(*args, **options)
