import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from crown_api.exports.models import ExportAuditLog


@pytest.mark.django_db
def test_export_creates_audit_log_row(client):
    # Arrange: finance user (exports are finance-gated for some endpoints)
    User = get_user_model()
    user = User.objects.create_user(username="fin", password="pw")
    finance_group, _ = Group.objects.get_or_create(name="Business Manager")
    user.groups.add(finance_group)

    client.force_login(user)

    # Act
    resp = client.get("/api/exports/invoices.csv")

    # Assert
    assert resp.status_code in (200, 403)
    assert ExportAuditLog.objects.filter(export_name="invoices.csv", user=user).exists()
