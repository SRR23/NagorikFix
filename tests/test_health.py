def test_health_check(api_client):
    """Process is up — smoke test for the NagorikFix API."""
    response = api_client.get("/api/health/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "nagorikfix-api"
