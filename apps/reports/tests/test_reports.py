"""End-to-end report flow: Nagorik → Administration → Staff."""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import User
from utils.constants import STATUS_ASSIGNED, STATUS_PENDING


def _jpeg(name="photo.jpg"):
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), color=(120, 40, 40)).save(buffer, format="JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


@pytest.fixture
def admin_user(db, dhaka_district):
    return User.objects.create_user(
        phone="01720000001",
        password="testpass123",
        full_name="Admin One",
        role=User.Role.ADMINISTRATION,
        district=dhaka_district,
        is_approved=True,
    )


@pytest.fixture
def staff_user(db, dhaka_district):
    return User.objects.create_user(
        phone="01720000002",
        password="testpass123",
        full_name="Staff One",
        role=User.Role.STAFF,
        district=dhaka_district,
        is_approved=True,
    )


@pytest.mark.django_db
def test_nagorik_submits_report_with_photos(nagorik_user, road_category):
    client = APIClient()
    client.force_authenticate(user=nagorik_user)

    response = client.post(
        "/api/reports/",
        {
            "category_id": str(road_category.id),
            "union": "Tejgaon",
            "ward": "Ward 24",
            "description": "Big pothole near the school gate causing accidents.",
            "photos": _jpeg(),
        },
        format="multipart",
    )
    assert response.status_code == 201, response.content
    data = response.json()
    assert data["status"] == STATUS_PENDING
    assert data["union"] == "Tejgaon"
    assert data["ward"] == "Ward 24"
    assert data["district"]["code"] == "dhaka"
    assert len(data["media"]) == 1


@pytest.mark.django_db
def test_admin_sees_district_report_and_assigns_staff(
    nagorik_user, admin_user, staff_user, road_category
):
    nagorik_client = APIClient()
    nagorik_client.force_authenticate(user=nagorik_user)
    created = nagorik_client.post(
        "/api/reports/",
        {
            "category_id": str(road_category.id),
            "union": "Mirpur",
            "ward": "Ward 7",
            "description": "Broken street light on the main road for 2 weeks.",
        },
        format="multipart",
    )
    assert created.status_code == 201
    report_id = created.json()["id"]

    admin_client = APIClient()
    admin_client.force_authenticate(user=admin_user)

    inbox = admin_client.get("/api/admin/reports/?status=pending")
    assert inbox.status_code == 200
    assert any(r["id"] == report_id for r in inbox.json()["results"])

    staff_list = admin_client.get("/api/admin/staff/")
    assert staff_list.status_code == 200
    assert any(s["id"] == staff_user.id for s in staff_list.json())

    assigned = admin_client.post(
        f"/api/admin/reports/{report_id}/assign/",
        {"staff_id": staff_user.id},
        format="json",
    )
    assert assigned.status_code == 200, assigned.content
    assert assigned.json()["status"] == STATUS_ASSIGNED
    assert assigned.json()["assigned_to"] == staff_user.id


@pytest.mark.django_db
def test_staff_updates_assigned_task(nagorik_user, admin_user, staff_user, road_category):
    nagorik_client = APIClient()
    nagorik_client.force_authenticate(user=nagorik_user)
    report_id = nagorik_client.post(
        "/api/reports/",
        {
            "category_id": str(road_category.id),
            "union": "Uttara",
            "ward": "Ward 1",
            "description": "Open drain overflowing after rain every day.",
        },
        format="multipart",
    ).json()["id"]

    admin_client = APIClient()
    admin_client.force_authenticate(user=admin_user)
    admin_client.post(
        f"/api/admin/reports/{report_id}/assign/",
        {"staff_id": staff_user.id},
        format="json",
    )

    staff_client = APIClient()
    staff_client.force_authenticate(user=staff_user)
    tasks = staff_client.get("/api/staff/tasks/")
    assert any(t["id"] == report_id for t in tasks.json()["results"])

    updated = staff_client.patch(
        f"/api/staff/tasks/{report_id}/status/",
        {"status": "in_progress"},
        format="json",
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"


@pytest.mark.django_db
def test_service_rejects_more_than_three_photos(nagorik_user, road_category):
    from rest_framework.exceptions import ValidationError

    from apps.reports.services import create_report_with_photos

    with pytest.raises(ValidationError):
        create_report_with_photos(
            nagorik=nagorik_user,
            validated_data={
                "category": road_category,
                "union": "Motijheel",
                "ward": "Ward 32",
                "description": "Garbage piled up blocking the roadside drain completely.",
            },
            photos=[_jpeg("a.jpg"), _jpeg("b.jpg"), _jpeg("c.jpg"), _jpeg("d.jpg")],
        )
