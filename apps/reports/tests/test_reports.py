"""Basic report create / list smoke tests."""
import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_create_anonymous_report(api_client, road_category):
    payload = {
        "category_id": str(road_category.id),
        "latitude": "23.810300",
        "longitude": "90.412500",
        "description": "Large pothole near the intersection",
        "is_anonymous": True,
    }
    response = api_client.post("/api/reports/", payload, format="json")
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["is_anonymous"] is True
    assert data["category"]["slug"] == "road"


@pytest.mark.django_db
def test_citizen_creates_and_lists_own_report(citizen_user, road_category):
    client = APIClient()
    client.force_authenticate(user=citizen_user)

    payload = {
        "category_id": str(road_category.id),
        "latitude": "23.750000",
        "longitude": "90.390000",
        "title": "Broken street light",
        "is_anonymous": False,
    }
    create = client.post("/api/reports/", payload, format="json")
    assert create.status_code == 201

    listing = client.get("/api/reports/")
    assert listing.status_code == 200
    results = listing.json()["results"]
    assert any(r["id"] == create.json()["id"] for r in results)


@pytest.mark.django_db
def test_list_categories(api_client, road_category):
    response = api_client.get("/api/categories/")
    assert response.status_code == 200
    assert any(c["slug"] == "road" for c in response.json()["results"])
