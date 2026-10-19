from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("email", "username", "role", "is_staff", "is_active", "date_joined")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "username", "first_name", "last_name", "phone")
    ordering = ("email",)

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("NagorikFix profile", {"fields": ("role", "phone")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("NagorikFix profile", {"fields": ("role", "phone", "email")}),
    )
