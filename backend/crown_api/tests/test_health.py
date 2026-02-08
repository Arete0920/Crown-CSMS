import pytest
from django.test import Client


@pytest.mark.django_db
def test_health_endpoint():
    """Test /health/ returns correct structure with build_sha."""
    client = Client()
    response = client.get("/health/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "ok" in data
    assert "status" in data
    assert "build_sha" in data
    
    assert isinstance(data["build_sha"], str)
    assert len(data["build_sha"]) > 0
    assert data["build_sha"] != ""
