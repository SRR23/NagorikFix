"""Serializers for registration, login, and profile."""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Public profile shape returned by /auth/me/ and register."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
            "role",
            "date_joined",
        )
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """
    Citizen self-registration.

    Admin / field_officer accounts should be created by staff later
    (or seeded) — not via public register.
    """

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
            "password",
            "password_confirm",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data, role=User.Role.CITIZEN)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Email + password login payload."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
