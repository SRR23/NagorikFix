"""Auth register / login / approval tests."""
import pytest


@pytest.mark.django_db
def test_register_nagorik_gets_tokens(api_client, dhaka_district):
    payload = {
        "phone": "01712223344",
        "password": "StrongPass123!",
        "password_confirm": "StrongPass123!",
        "full_name": "Karim Nagorik",
        "role": "nagorik",
        "district_id": dhaka_district.id,
    }
    response = api_client.post("/api/auth/register/", payload, format="json")
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["role"] == "nagorik"
    assert body["user"]["is_approved"] is True
    assert "tokens" in body
    assert body["user"]["district"]["code"] == "dhaka"


@pytest.mark.django_db
def test_register_staff_pending_no_tokens(api_client, dhaka_district):
    payload = {
        "phone": "01812223344",
        "password": "StrongPass123!",
        "password_confirm": "StrongPass123!",
        "full_name": "Staff Person",
        "role": "staff",
        "district_id": dhaka_district.id,
    }
    response = api_client.post("/api/auth/register/", payload, format="json")
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["is_approved"] is False
    assert "tokens" not in body


@pytest.mark.django_db
def test_login_pending_staff_forbidden(api_client, dhaka_district):
    from apps.accounts.models import User

    User.objects.create_user(
        phone="01912223344",
        password="StrongPass123!",
        full_name="Pending Staff",
        role=User.Role.STAFF,
        district=dhaka_district,
        is_approved=False,
    )
    response = api_client.post(
        "/api/auth/login/",
        {"phone": "01912223344", "password": "StrongPass123!"},
        format="json",
    )
    assert response.status_code == 403
    assert response.json()["error"] == "account_pending_approval"


@pytest.mark.django_db
def test_login_nagorik(api_client, nagorik_user):
    response = api_client.post(
        "/api/auth/login/",
        {"phone": "01711111111", "password": "testpass123"},
        format="json",
    )
    assert response.status_code == 200
    assert "access" in response.json()["tokens"]


@pytest.mark.django_db
def test_list_districts(api_client, dhaka_district):
    response = api_client.get("/api/districts/")
    assert response.status_code == 200
    assert any(d["code"] == "dhaka" for d in response.json())
