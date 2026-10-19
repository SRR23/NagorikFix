"""Report routes (mounted under /api/)."""
from django.urls import path

from apps.reports.views import (
    AdminDashboardStatsView,
    CategoryListView,
    ReportDetailView,
    ReportListCreateView,
    ReportMediaUploadView,
    ReportUpdateView,
)

app_name = "reports"

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("reports/", ReportListCreateView.as_view(), name="report-list-create"),
    path(
        "reports/<uuid:report_id>/",
        ReportDetailView.as_view(),
        name="report-detail",
    ),
    path(
        "reports/<uuid:report_id>/update/",
        ReportUpdateView.as_view(),
        name="report-update",
    ),
    path(
        "reports/<uuid:report_id>/media/",
        ReportMediaUploadView.as_view(),
        name="report-media-upload",
    ),
    path(
        "admin/dashboard/stats/",
        AdminDashboardStatsView.as_view(),
        name="admin-dashboard-stats",
    ),
]
