"""
NagorikFix accounts.

- Login identity: phone (unique)
- Roles: nagorik | staff | administration
- Each user belongs to exactly one District
- Staff / Administration need is_approved=True before login works
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from apps.accounts.phone import normalize_bd_phone


class District(models.Model):
    """Bangladesh district — required on signup; scopes user work area."""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    name_bn = models.CharField(max_length=100, blank=True)
    code = models.CharField(max_length=32, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class UserManager(BaseUserManager):
    """Create users with phone as USERNAME_FIELD."""

    use_in_migrations = True

    def _create_user(self, phone, password, **extra_fields):
        if not phone:
            raise ValueError("Phone number is required.")

        phone = normalize_bd_phone(phone)
        extra_fields.setdefault("username", phone)

        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_approved", True)
        extra_fields.setdefault("role", User.Role.ADMINISTRATION)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(phone, password, **extra_fields)


class User(AbstractUser):
    """
    Platform user.

    Note: Django's built-in ``is_staff`` means "can open /admin/".
    Our role ``staff`` means field staff — use ``is_staff_member`` for that.
    """

    class Role(models.TextChoices):
        NAGORIK = "nagorik", "Nagorik"
        STAFF = "staff", "Staff"
        ADMINISTRATION = "administration", "Administration"

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, unique=True, db_index=True)
    full_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.NAGORIK,
        db_index=True,
    )
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
        help_text="Required for normal signup; may be empty only for bootstrap superuser.",
    )
    # Nagorik: True immediately. Staff/Administration: False until approved.
    is_approved = models.BooleanField(default=False, db_index=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["phone"]

    def __str__(self) -> str:
        return f"{self.phone} ({self.role})"

    def save(self, *args, **kwargs):
        if self.phone:
            self.phone = normalize_bd_phone(self.phone)
            # Keep AbstractUser.username in sync (still required & unique).
            if not self.username:
                self.username = self.phone
        super().save(*args, **kwargs)

    @property
    def is_nagorik(self) -> bool:
        return self.role == self.Role.NAGORIK

    @property
    def is_staff_member(self) -> bool:
        """Field staff role — not Django admin ``is_staff``."""
        return self.role == self.Role.STAFF

    @property
    def is_administration(self) -> bool:
        return self.role == self.Role.ADMINISTRATION

    @property
    def can_use_app(self) -> bool:
        """Login / API access allowed."""
        if self.is_superuser:
            return True
        return self.is_active and self.is_approved
