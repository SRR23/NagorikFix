"""Auth register / login smoke tests."""
import pytest


@pytest.mark.django_db
def test_register_and_me(api_client):
    payload = {
        "email": "new.citizen@example.com",
        "username": "newcitizen",
        "first_name": "New",
        "last_name": "Citizen",
        "password": "StrongPass123!",
        "password_confirm": "StrongPass123!",
    }
    response = api_client.post("/api/auth/register/", payload, format="json")
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["role"] == "citizen"
    assert "access" in body["tokens"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {body['tokens']['access']}")
    me = api_client.get("/api/auth/me/")
    assert me.status_code == 200
    assert me.json()["email"] == "new.citizen@example.com"


@pytest.mark.django_db
def test_login(api_client, citizen_user):
    response = api_client.post(
        "/api/auth/login/",
        {"email": "citizen@example.com", "password": "testpass123"},
        format="json",
    )
    assert response.status_code == 200
    assert "access" in response.json()["tokens"]
