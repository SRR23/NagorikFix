from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import District, User


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "name_bn", "code", "is_active")
    search_fields = ("name", "name_bn", "code")
    list_filter = ("is_active",)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "phone",
        "full_name",
        "role",
        "district",
        "is_approved",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("role", "is_approved", "district", "is_staff", "is_active")
    search_fields = ("phone", "full_name", "email")
    ordering = ("phone",)

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (
            "Profile",
            {"fields": ("full_name", "email", "role", "district", "is_approved")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "phone",
                    "full_name",
                    "role",
                    "district",
                    "is_approved",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    # AbstractUser admin expects username; we use phone instead.
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "username" in form.base_fields:
            form.base_fields["username"].required = False
        return form
