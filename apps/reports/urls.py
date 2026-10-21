"""Report routes (mounted under /api/)."""
from django.urls import path

from apps.reports.views import (
    AdminAssignReportView,
    AdminDashboardStatsView,
    AdminRejectReportView,
    AdminReportDetailView,
    AdminReportInboxView,
    AdminSetPriorityView,
    AdminStaffListView,
    CategoryListView,
    NagorikReportDetailView,
    NagorikReportListCreateView,
    StaffTaskDetailView,
    StaffTaskListView,
    StaffUpdateStatusView,
)

app_name = "reports"

urlpatterns = [
    # Shared
    path("categories/", CategoryListView.as_view(), name="category-list"),
    # Nagorik
    path("reports/", NagorikReportListCreateView.as_view(), name="report-list-create"),
    path(
        "reports/<uuid:report_id>/",
        NagorikReportDetailView.as_view(),
        name="report-detail",
    ),
    # Administration
    path("admin/reports/", AdminReportInboxView.as_view(), name="admin-report-inbox"),
    path(
        "admin/reports/<uuid:report_id>/",
        AdminReportDetailView.as_view(),
        name="admin-report-detail",
    ),
    path(
        "admin/reports/<uuid:report_id>/assign/",
        AdminAssignReportView.as_view(),
        name="admin-report-assign",
    ),
    path(
        "admin/reports/<uuid:report_id>/priority/",
        AdminSetPriorityView.as_view(),
        name="admin-report-priority",
    ),
    path(
        "admin/reports/<uuid:report_id>/reject/",
        AdminRejectReportView.as_view(),
        name="admin-report-reject",
    ),
    path("admin/staff/", AdminStaffListView.as_view(), name="admin-staff-list"),
    path(
        "admin/dashboard/stats/",
        AdminDashboardStatsView.as_view(),
        name="admin-dashboard-stats",
    ),
    # Staff
    path("staff/tasks/", StaffTaskListView.as_view(), name="staff-task-list"),
    path(
        "staff/tasks/<uuid:report_id>/",
        StaffTaskDetailView.as_view(),
        name="staff-task-detail",
    ),
    path(
        "staff/tasks/<uuid:report_id>/status/",
        StaffUpdateStatusView.as_view(),
        name="staff-task-status",
    ),
]
