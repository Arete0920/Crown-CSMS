import pytest


@pytest.mark.django_db
def test_missing_school_id_rejected(client, django_user_model):
    user = django_user_model.objects.create_user(username="board_tenant_test", password="x")
    client.force_login(user)
    # No X-School-Id header — should get 400 (ValidationError) or 403 (no permission)
    resp = client.get("/api/board/metrics/")
    assert resp.status_code in (400, 403)
