"""Role-based DRF permissions for the civic platform."""
from rest_framework.permissions import BasePermission


class IsCitizen(BasePermission):
    message = "Citizen account required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "is_citizen", False)
        )


class IsAuthorityAdmin(BasePermission):
    """District / city-corp style admin (role=admin) or Django superuser."""

    message = "Authority admin access required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (
                getattr(user, "is_authority_admin", False)
                or getattr(user, "is_superuser", False)
            )
        )


class IsFieldOfficer(BasePermission):
    message = "Field officer account required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "is_field_officer", False)
        )


class IsAdminOrFieldOfficer(BasePermission):
    message = "Admin or field officer access required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return bool(
            getattr(user, "is_authority_admin", False)
            or getattr(user, "is_field_officer", False)
            or getattr(user, "is_superuser", False)
        )
