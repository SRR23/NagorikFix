"""
Infrastructure complaint tickets.

Flow:
1. Nagorik submits: category + union + ward + description + up to 3 photos
2. District Administration reviews pending reports
3. Administration assigns a Staff member in the same district
4. Staff works the ticket (in_progress → resolved)
"""
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models import District
from utils.constants import (
    MAX_REPORT_PHOTOS,
    MEDIA_IMAGE,
    MEDIA_TYPE_CHOICES,
    PRIORITY_CHOICES,
    PRIORITY_MEDIUM,
    REPORT_STATUS_CHOICES,
    STATUS_PENDING,
)


class Category(models.Model):
    """Problem category (Road, Drainage, Electricity, …)."""

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
    """A Nagorik infrastructure complaint for one district."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="reports",
    )
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="reports",
        help_text="Copied from the reporter's district at submit time.",
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_reports",
    )

    # Local area fields filled by Nagorik on the form.
    union = models.CharField(max_length=120)
    ward = models.CharField(max_length=120)
    description = models.TextField()

    # Optional GPS if the mobile client sends it.
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

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
        limit_choices_to={"role": "staff"},
    )
    assigned_at = models.DateTimeField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports_assigned",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["district", "status"]),
            models.Index(fields=["status", "priority"]),
        ]

    def __str__(self) -> str:
        return f"{self.category} · {self.union}/{self.ward} [{self.status}]"


class ReportMedia(models.Model):
    """Photo attached to a report (citizen evidence or staff before/after)."""

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
    file = models.ImageField(upload_to="reports/%Y/%m/")
    media_type = models.CharField(
        max_length=16,
        choices=MEDIA_TYPE_CHOICES,
        default=MEDIA_IMAGE,
    )
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
        return f"{self.kind} for {self.report_id}"

    def clean(self):
        if self.kind == self.Kind.CITIZEN and self.report_id:
            existing = self.report.media.filter(kind=self.Kind.CITIZEN)
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.count() >= MAX_REPORT_PHOTOS:
                raise ValidationError(
                    f"Maximum {MAX_REPORT_PHOTOS} photos allowed per report."
                )
