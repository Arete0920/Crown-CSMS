from core.observability.sentry import before_send


def test_before_send_removes_request_payload_and_sensitive_headers():
    event = {
        "request": {
            "data": {"password": "secret", "student_name": "Example Student"},
            "cookies": {"sessionid": "secret"},
            "query_string": "token=secret",
            "headers": {
                "Authorization": "Bearer secret",
                "Cookie": "sessionid=secret",
                "X-Api-Key": "secret",
                "User-Agent": "pytest",
            },
        },
        "user": {
            "id": "internal-user-id",
            "email": "person@example.test",
            "username": "person",
        },
    }

    sanitized = before_send(event, {})

    assert "data" not in sanitized["request"]
    assert "cookies" not in sanitized["request"]
    assert "query_string" not in sanitized["request"]
    assert sanitized["request"]["headers"]["Authorization"] == "[Filtered]"
    assert sanitized["request"]["headers"]["Cookie"] == "[Filtered]"
    assert sanitized["request"]["headers"]["X-Api-Key"] == "[Filtered]"
    assert sanitized["request"]["headers"]["User-Agent"] == "pytest"
    assert sanitized["user"] == {"id": "internal-user-id"}
