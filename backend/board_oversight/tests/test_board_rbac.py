import pytest
TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

SCHOOL_ID = "00000000-0000-0000-0000-000000000000"


@pytest.mark.django_db
def test_non_board_user_forbidden(client, django_user_model):
    user = django_user_model.objects.create_user("rbac_test_non_board", None, TEST_AUTH_SECRET)
    client.force_login(user)
    resp = client.get(
        "/api/board/metrics/",
        HTTP_X_SCHOOL_ID=SCHOOL_ID,
    )
    assert resp.status_code in (403, 404)




