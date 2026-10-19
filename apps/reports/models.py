"""
Core domain models for infrastructure complaint tickets.

MVP keeps this intentionally small:
- Category (road, drainage, electricity, …)
- Report (geo + status + priority)
- ReportMedia (photo / short video proof)
"""
import uuid

from django.conf import settings
from django.db import models

from utils.constants import (
    MEDIA_TYPE_CHOICES,
    PRIORITY_CHOICES,
    PRIORITY_MEDIUM,
    REPORT_STATUS_CHOICES,
    STATUS_PENDING,
)


class Category(models.Model):
    """One-click report category (Road, Drainage, Electricity, …)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


class Report(models.Model):
    """
    A citizen infrastructure complaint / ticket.

    Location is stored as lat/lng for map pins. Address text is optional
    (reverse-geocode can fill it later).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="reports",
    )
    # Null when the citizen chooses anonymous reporting.
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_reports",
    )
    is_anonymous = models.BooleanField(default=False)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address_text = models.CharField(max_length=500, blank=True)

    status = models.CharField(
        max_length=32,
        choices=REPORT_STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    priority = models.CharField(
        max_length=16,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        db_index=True,
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_reports",
        limit_choices_to={"role": "field_officer"},
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self) -> str:
        return f"{self.category} @ ({self.latitude}, {self.longitude}) [{self.status}]"


class ReportMedia(models.Model):
    """Photo or short video attached to a report (citizen or before/after proof)."""

    class Kind(models.TextChoices):
        CITIZEN = "citizen", "Citizen evidence"
        BEFORE = "before", "Before work"
        AFTER = "after", "After work"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="media",
    )
    file = models.FileField(upload_to="reports/%Y/%m/")
    media_type = models.CharField(max_length=16, choices=MEDIA_TYPE_CHOICES)
    kind = models.CharField(
        max_length=16,
        choices=Kind.choices,
        default=Kind.CITIZEN,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_media",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "report media"

    def __str__(self) -> str:
        return f"{self.kind} {self.media_type} for {self.report_id}"
