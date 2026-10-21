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
        "district",
        "union",
        "ward",
        "status",
        "priority",
        "assigned_to",
        "created_at",
    )
    list_filter = ("status", "priority", "category", "district")
    search_fields = ("union", "ward", "description")
    raw_id_fields = ("reporter", "assigned_to", "assigned_by")
    autocomplete_fields = ("district",)
    inlines = [ReportMediaInline]
