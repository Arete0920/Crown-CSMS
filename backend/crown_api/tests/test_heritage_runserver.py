"""The demo's larger listener queue must never create a hosted access path."""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.core.management.base import CommandError
from django.core.management.commands.runserver import Command as RunserverCommand

from crown_api.management.commands.heritage_runserver import (
    Command,
    HeritageLocalWSGIServer,
)


LOCAL_ENV = {
    "CROWN_ENV": "local",
    "DJANGO_ENV": "local",
    "VITE_LOCAL_DEMO": "1",
}
LOCAL_OPTIONS = {"addrport": "127.0.0.1:8000", "use_reloader": False}


def test_heritage_server_is_burst_safe_and_not_global() -> None:
    """Increase the local accept queue without altering Django's default."""
    assert HeritageLocalWSGIServer.request_queue_size == 128
    assert Command.server_cls is HeritageLocalWSGIServer
    assert RunserverCommand.server_cls is not HeritageLocalWSGIServer


def test_heritage_server_accepts_only_explicit_local_configuration() -> None:
    """The approved local launch delegates to the usual Django runserver."""
    settings_stub = SimpleNamespace(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3"}},
    )
    with (
        patch.dict(os.environ, LOCAL_ENV, clear=True),
        patch("crown_api.management.commands.heritage_runserver.settings", settings_stub),
        patch.object(RunserverCommand, "handle", return_value="local") as delegate,
    ):
        assert Command().handle(**LOCAL_OPTIONS) == "local"
    delegate.assert_called_once_with(**LOCAL_OPTIONS)


@pytest.mark.parametrize(
    ("environment_override", "options_override", "debug", "engine"),
    [
        ({"CROWN_ENV": "prod"}, {}, True, "django.db.backends.sqlite3"),
        ({"DJANGO_ENV": "staging"}, {}, True, "django.db.backends.sqlite3"),
        ({"VITE_LOCAL_DEMO": "0"}, {}, True, "django.db.backends.sqlite3"),
        ({"WEBSITE_HOSTNAME": "example.azurewebsites.net"}, {}, True, "django.db.backends.sqlite3"),
        ({"WEBSITE_INSTANCE_ID": "hosted"}, {}, True, "django.db.backends.sqlite3"),
        ({"AZURE_ENVIRONMENT": "dev"}, {}, True, "django.db.backends.sqlite3"),
        ({}, {"addrport": "0.0.0.0:8000"}, True, "django.db.backends.sqlite3"),
        ({}, {"addrport": "127.0.0.1:8001"}, True, "django.db.backends.sqlite3"),
        ({}, {"use_reloader": True}, True, "django.db.backends.sqlite3"),
        ({}, {}, False, "django.db.backends.sqlite3"),
        ({}, {}, True, "django.db.backends.postgresql"),
    ],
)
def test_heritage_server_refuses_unapproved_runtime(
    environment_override: dict[str, str],
    options_override: dict[str, object],
    debug: bool,
    engine: str,
) -> None:
    """Every production, remote, unexpected database and reload path fails."""
    environment = {**LOCAL_ENV, **environment_override}
    options = {**LOCAL_OPTIONS, **options_override}
    settings_stub = SimpleNamespace(
        DEBUG=debug,
        DATABASES={"default": {"ENGINE": engine}},
    )
    with (
        patch.dict(os.environ, environment, clear=True),
        patch("crown_api.management.commands.heritage_runserver.settings", settings_stub),
        patch.object(RunserverCommand, "handle", return_value="not-called") as delegate,
    ):
        with pytest.raises(CommandError, match="hosted execution is forbidden"):
            Command().handle(**options)
    delegate.assert_not_called()
