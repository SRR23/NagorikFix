from django.contrib import admin

from apps.reports.models import Category, Report, ReportMedia


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")


class ReportMediaInline(admin.TabularInline):
    model = ReportMedia
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "category",
        "status",
        "priority",
        "is_anonymous",
        "assigned_to",
        "created_at",
    )
    list_filter = ("status", "priority", "category", "is_anonymous")
    search_fields = ("title", "description", "address_text")
    raw_id_fields = ("reporter", "assigned_to")
    inlines = [ReportMediaInline]
