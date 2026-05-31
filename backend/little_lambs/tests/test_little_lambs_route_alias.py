def test_little_lambs_alias_matches_aftercare(client):
    aftercare_response = client.get("/api/v1/aftercare/config/")
    little_lambs_response = client.get("/api/v1/little-lambs/config/")

    assert little_lambs_response.status_code == aftercare_response.status_code
    assert little_lambs_response.content == aftercare_response.content
