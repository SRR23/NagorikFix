"""
Report domain services — keep workflow rules out of views.
"""
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import User
from apps.reports.models import Report, ReportMedia
from utils.constants import (
    MAX_REPORT_PHOTOS,
    MEDIA_IMAGE,
    STATUS_ASSIGNED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    STATUS_RESOLVED,
)


def create_report_with_photos(*, nagorik: User, validated_data: dict, photos: list):
    """
    Create a report for a logged-in Nagorik and attach up to 3 photos.

    District always comes from the Nagorik profile — not from the client.
    """
    if not nagorik.district_id:
        raise ValidationError(
            {"district": "Your account has no district. Contact support."}
        )

    if len(photos) > MAX_REPORT_PHOTOS:
        raise ValidationError(
            {"photos": f"Maximum {MAX_REPORT_PHOTOS} photos allowed."}
        )

    category = validated_data.pop("category")

    with transaction.atomic():
        report = Report.objects.create(
            category=category,
            district_id=nagorik.district_id,
            reporter=nagorik,
            status=STATUS_PENDING,
            **validated_data,
        )
        for photo in photos:
            ReportMedia.objects.create(
                report=report,
                file=photo,
                media_type=MEDIA_IMAGE,
                kind=ReportMedia.Kind.CITIZEN,
                uploaded_by=nagorik,
            )
    return report


def assign_report_to_staff(*, report: Report, staff: User, admin: User) -> Report:
    """
    Administration assigns a pending/open report to staff in the same district.
    """
    if not (admin.is_superuser or admin.is_administration):
        raise PermissionDenied("Only administration can assign reports.")

    if not admin.is_superuser and report.district_id != admin.district_id:
        raise PermissionDenied("You can only assign reports in your district.")

    if staff.role != User.Role.STAFF or not staff.is_approved:
        raise ValidationError({"staff_id": "Select an approved staff member."})

    if staff.district_id != report.district_id:
        raise ValidationError(
            {"staff_id": "Staff must belong to the same district as the report."}
        )

    if report.status in {STATUS_RESOLVED, STATUS_REJECTED}:
        raise ValidationError(
            {"detail": "Cannot assign a resolved or rejected report."}
        )

    report.assigned_to = staff
    report.assigned_by = admin
    report.assigned_at = timezone.now()
    report.status = STATUS_ASSIGNED
    report.save(
        update_fields=[
            "assigned_to",
            "assigned_by",
            "assigned_at",
            "status",
            "updated_at",
        ]
    )
    return report


def staff_update_status(*, report: Report, staff: User, status: str) -> Report:
    """Staff may progress their own assigned tickets."""
    if report.assigned_to_id != staff.id:
        raise PermissionDenied("This report is not assigned to you.")

    allowed = {STATUS_IN_PROGRESS, STATUS_RESOLVED}
    if status not in allowed:
        raise ValidationError(
            {"status": f"Staff may only set: {', '.join(sorted(allowed))}."}
        )

    report.status = status
    if status == STATUS_RESOLVED:
        report.resolved_at = timezone.now()
    else:
        report.resolved_at = None
    report.save(update_fields=["status", "resolved_at", "updated_at"])
    return report


def admin_set_priority(*, report: Report, admin: User, priority: str) -> Report:
    if not admin.is_superuser and report.district_id != admin.district_id:
        raise PermissionDenied("You can only manage reports in your district.")
    report.priority = priority
    report.save(update_fields=["priority", "updated_at"])
    return report


def admin_reject_report(*, report: Report, admin: User) -> Report:
    if not admin.is_superuser and report.district_id != admin.district_id:
        raise PermissionDenied("You can only manage reports in your district.")
    report.status = STATUS_REJECTED
    report.save(update_fields=["status", "updated_at"])
    return report
