import pytest

SCHOOL_ID = "00000000-0000-0000-0000-000000000000"


@pytest.mark.django_db
def test_non_board_user_forbidden(client, django_user_model):
    user = django_user_model.objects.create_user(username="rbac_test_non_board", password="x")
    client.force_login(user)
    resp = client.get(
        "/api/board/metrics/",
        HTTP_X_SCHOOL_ID=SCHOOL_ID,
    )
    assert resp.status_code == 403
