"""Report serializers for Nagorik / Administration / Staff flows."""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import DistrictSerializer
from apps.reports.models import Category, Report, ReportMedia
from utils.constants import MAX_REPORT_PHOTOS, PRIORITY_CHOICES

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "sort_order")


class ReportMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportMedia
        fields = ("id", "file", "media_type", "kind", "created_at")
        read_only_fields = fields


class StaffBriefSerializer(serializers.ModelSerializer):
    """Compact staff row for Administration assign dropdown."""

    class Meta:
        model = User
        fields = ("id", "phone", "full_name")
        read_only_fields = fields


class ReporterBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "phone", "full_name")
        read_only_fields = fields


class ReportListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    district = DistrictSerializer(read_only=True)
    photo_count = serializers.IntegerField(read_only=True)
    assigned_to_name = serializers.CharField(
        source="assigned_to.full_name", read_only=True, allow_null=True
    )

    class Meta:
        model = Report
        fields = (
            "id",
            "category",
            "district",
            "union",
            "ward",
            "description",
            "status",
            "priority",
            "photo_count",
            "assigned_to",
            "assigned_to_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ReportDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    district = DistrictSerializer(read_only=True)
    media = ReportMediaSerializer(many=True, read_only=True)
    reporter = ReporterBriefSerializer(read_only=True)
    assigned_to_detail = StaffBriefSerializer(source="assigned_to", read_only=True)

    class Meta:
        model = Report
        fields = (
            "id",
            "category",
            "district",
            "reporter",
            "union",
            "ward",
            "description",
            "latitude",
            "longitude",
            "status",
            "priority",
            "assigned_to",
            "assigned_to_detail",
            "assigned_at",
            "media",
            "created_at",
            "updated_at",
            "resolved_at",
        )
        read_only_fields = fields


class ReportCreateSerializer(serializers.Serializer):
    """
    Nagorik submit form.

    Multipart fields:
    - category_id, union, ward, description (required)
    - photos: up to 3 image files (optional but recommended)
    - latitude, longitude (optional)
    """

    category_id = serializers.UUIDField()
    union = serializers.CharField(max_length=120)
    ward = serializers.CharField(max_length=120)
    description = serializers.CharField()
    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )

    def validate_description(self, value):
        text = (value or "").strip()
        if len(text) < 10:
            raise serializers.ValidationError(
                "Please describe the problem (at least 10 characters)."
            )
        return text

    def validate_union(self, value):
        return value.strip()

    def validate_ward(self, value):
        return value.strip()

    def validate(self, attrs):
        category_id = attrs.pop("category_id")
        try:
            attrs["category"] = Category.objects.get(pk=category_id, is_active=True)
        except Category.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"category_id": "Unknown or inactive category."}
            ) from exc
        return attrs


class AssignReportSerializer(serializers.Serializer):
    staff_id = serializers.IntegerField()

    def validate(self, attrs):
        try:
            attrs["staff"] = User.objects.get(
                pk=attrs["staff_id"],
                role=User.Role.STAFF,
                is_approved=True,
            )
        except User.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"staff_id": "Approved staff member not found."}
            ) from exc
        return attrs


class StaffStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["in_progress", "resolved"])


class AdminPrioritySerializer(serializers.Serializer):
    priority = serializers.ChoiceField(choices=PRIORITY_CHOICES)
