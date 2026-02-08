import pytest
from django.test import Client


@pytest.mark.django_db
def test_health_endpoint():
    """Test /health/ returns correct structure with build_sha."""
    client = Client()
    response = client.get("/health/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Required fields
    assert "ok" in data
    assert "status" in data
    assert "build_sha" in data
    assert "env" in data
    assert "build_time_utc" in data
    assert "version" in data
    assert "db" in data
    
    # build_sha validation: must be 40-char hex or "local-dev"
    build_sha = data["build_sha"]
    assert isinstance(build_sha, str)
    assert len(build_sha) > 0
    if build_sha != "local-dev":
        assert len(build_sha) == 40, f"build_sha must be 40 chars (got {len(build_sha)})"
        assert all(c in "0123456789abcdef" for c in build_sha.lower()), "build_sha must be hex"
    
    # db status validation
    assert data["db"] in ["ok", "unreachable"]
