import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_export_console_admin_view_loads(admin_client):
    url = reverse("admin:exports_exportauditlog_console")
    resp = admin_client.get(url)
    assert resp.status_code == 200
    assert b"Export Console" in resp.content
