"""
Custom user model for the NagorikFix platform.

Roles:
- citizen: submits infrastructure reports
- admin: authority dashboard (district / city corp)
- field_officer: assigned field tasks and proof uploads
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Platform user. Email is the login identity."""

    class Role(models.TextChoices):
        CITIZEN = "citizen", "Citizen"
        ADMIN = "admin", "Admin"
        FIELD_OFFICER = "field_officer", "Field Officer"

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.CITIZEN,
        db_index=True,
    )

    # Prefer email over username for API login.
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ["email"]

    def __str__(self) -> str:
        return f"{self.email} ({self.role})"

    @property
    def is_citizen(self) -> bool:
        return self.role == self.Role.CITIZEN

    @property
    def is_authority_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_field_officer(self) -> bool:
        return self.role == self.Role.FIELD_OFFICER
