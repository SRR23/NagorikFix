"""Role-based DRF permissions for NagorikFix."""
from rest_framework.permissions import BasePermission


def _approved(user) -> bool:
    return bool(user and user.is_authenticated and getattr(user, "can_use_app", False))


class IsApprovedUser(BasePermission):
    message = "Approved account required."

    def has_permission(self, request, view):
        return _approved(request.user)


class IsNagorik(BasePermission):
    message = "Nagorik account required."

    def has_permission(self, request, view):
        user = request.user
        return _approved(user) and getattr(user, "is_nagorik", False)


class IsAdministration(BasePermission):
    """District administration role, or Django superuser."""

    message = "Administration access required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "is_superuser", False):
            return True
        return _approved(user) and getattr(user, "is_administration", False)


class IsStaffMember(BasePermission):
    message = "Staff account required."

    def has_permission(self, request, view):
        user = request.user
        return _approved(user) and getattr(user, "is_staff_member", False)


class IsAdministrationOrStaff(BasePermission):
    message = "Administration or staff access required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "is_superuser", False):
            return True
        if not getattr(user, "can_use_app", False):
            return False
        return bool(
            getattr(user, "is_administration", False)
            or getattr(user, "is_staff_member", False)
        )
