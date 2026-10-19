"""Report serializers — keep create payload short for one-click reporting."""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.reports.models import Category, Report, ReportMedia

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "sort_order")


class ReportMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportMedia
        fields = ("id", "file", "media_type", "kind", "created_at")
        read_only_fields = ("id", "created_at")


class ReportListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Report
        fields = (
            "id",
            "category",
            "category_id",
            "title",
            "status",
            "priority",
            "latitude",
            "longitude",
            "address_text",
            "is_anonymous",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "status", "created_at", "updated_at")


class ReportDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    media = ReportMediaSerializer(many=True, read_only=True)
    assigned_to_email = serializers.EmailField(
        source="assigned_to.email",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Report
        fields = (
            "id",
            "category",
            "title",
            "description",
            "status",
            "priority",
            "latitude",
            "longitude",
            "address_text",
            "is_anonymous",
            "assigned_to",
            "assigned_to_email",
            "media",
            "created_at",
            "updated_at",
            "resolved_at",
        )
        read_only_fields = fields


class ReportCreateSerializer(serializers.ModelSerializer):
    """
    Minimal create body for one-click reporting:
    category_id + GPS (+ optional description / anonymous flag).
    Media is uploaded in a follow-up call.
    """

    category_id = serializers.UUIDField()

    class Meta:
        model = Report
        fields = (
            "category_id",
            "title",
            "description",
            "latitude",
            "longitude",
            "address_text",
            "is_anonymous",
        )

    def validate_category_id(self, value):
        if not Category.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError("Unknown or inactive category.")
        return value

    def create(self, validated_data):
        category_id = validated_data.pop("category_id")
        request = self.context["request"]
        is_anonymous = validated_data.get("is_anonymous", False)

        reporter = None
        if request.user.is_authenticated and not is_anonymous:
            reporter = request.user

        return Report.objects.create(
            category_id=category_id,
            reporter=reporter,
            **validated_data,
        )


class ReportStatusUpdateSerializer(serializers.Serializer):
    """Admin / officer status or priority change."""

    status = serializers.ChoiceField(
        choices=Report._meta.get_field("status").choices,
        required=False,
    )
    priority = serializers.ChoiceField(
        choices=Report._meta.get_field("priority").choices,
        required=False,
    )
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.FIELD_OFFICER),
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs
