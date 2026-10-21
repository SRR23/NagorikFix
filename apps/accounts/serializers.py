"""Serializers for registration, login, profile, and districts."""
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.models import District, User
from apps.accounts.phone import normalize_bd_phone


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ("id", "name", "name_bn", "code")


class UserSerializer(serializers.ModelSerializer):
    """Public profile returned by /auth/me/ and register."""

    district = DistrictSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "phone",
            "full_name",
            "email",
            "role",
            "district",
            "is_approved",
            "date_joined",
        )
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    """
    Public signup for all three roles.

    - nagorik → is_approved=True, tokens returned
    - staff / administration → is_approved=False, no tokens until approved
    """

    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)
    full_name = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=User.Role.choices)
    district_id = serializers.IntegerField()
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate_phone(self, value):
        try:
            phone = normalize_bd_phone(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        return phone

    def validate_district_id(self, value):
        if not District.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError("Unknown or inactive district.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        try:
            validate_password(attrs["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        district_id = validated_data.pop("district_id")
        role = validated_data["role"]

        # Nagorik can use the app immediately; others wait for approval.
        is_approved = role == User.Role.NAGORIK

        return User.objects.create_user(
            password=password,
            district_id=district_id,
            is_approved=is_approved,
            **validated_data,
        )


class LoginSerializer(serializers.Serializer):
    """Phone + password login."""

    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)

    def validate_phone(self, value):
        try:
            return normalize_bd_phone(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
