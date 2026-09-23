import io
import pytest
from django.core.management import call_command


@pytest.fixture(autouse=True)
def scheduling_permission_registry(db):
    """Exercise real persistent permissions even when tests skip data migrations."""
    call_command('seed_permissions', stdout=io.StringIO())
