def test_legacy_daycare_alias_matches_aftercare(client):
    aftercare_response = client.get("/api/v1/aftercare/config/")
    legacy_response = client.get("/api/v1/little-lambs/config/")

    assert legacy_response.status_code == aftercare_response.status_code
    assert legacy_response.content == aftercare_response.content
