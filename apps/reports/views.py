"""
Role-scoped report APIs.

Nagorik  → submit + track own reports
Admin    → district inbox, list staff, assign
Staff    → assigned task list + status updates
"""
from django.db.models import Count, Prefetch, Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.reports.models import Category, Report, ReportMedia
from apps.reports.serializers import (
    AdminPrioritySerializer,
    AssignReportSerializer,
    CategorySerializer,
    ReportCreateSerializer,
    ReportDetailSerializer,
    ReportListSerializer,
    StaffBriefSerializer,
    StaffStatusSerializer,
)
from apps.reports.services import (
    admin_reject_report,
    admin_set_priority,
    assign_report_to_staff,
    create_report_with_photos,
    staff_update_status,
)
from utils.constants import MAX_REPORT_PHOTOS
from utils.permissions import IsAdministration, IsNagorik, IsStaffMember


def _report_queryset():
    return (
        Report.objects.select_related(
            "category",
            "district",
            "reporter",
            "assigned_to",
            "assigned_by",
        )
        .prefetch_related(
            Prefetch(
                "media",
                queryset=ReportMedia.objects.order_by("created_at"),
            )
        )
        .annotate(
            photo_count=Count(
                "media",
                filter=Q(media__kind=ReportMedia.Kind.CITIZEN),
            )
        )
    )


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------


@extend_schema(tags=["categories"])
class CategoryListView(generics.ListAPIView):
    """Active categories for the Nagorik report form."""

    serializer_class = CategorySerializer
    permission_classes = [IsNagorik]
    queryset = Category.objects.filter(is_active=True)
    pagination_class = None


# ---------------------------------------------------------------------------
# Nagorik
# ---------------------------------------------------------------------------


@extend_schema_view(
    get=extend_schema(tags=["reports"]),
    post=extend_schema(tags=["reports"]),
)
class NagorikReportListCreateView(generics.ListCreateAPIView):
    """
    GET  — Nagorik's own submitted reports
    POST — submit a new report (multipart: form fields + photos)
    """

    permission_classes = [IsNagorik]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return _report_queryset().filter(reporter=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ReportCreateSerializer
        return ReportListSerializer

    def create(self, request, *args, **kwargs):
        serializer = ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Accept photos as repeated "photos" keys or a single file.
        photos = request.FILES.getlist("photos")
        if not photos and request.FILES.get("photo"):
            photos = [request.FILES["photo"]]

        if len(photos) > MAX_REPORT_PHOTOS:
            return Response(
                {
                    "error": "validation_error",
                    "detail": {
                        "photos": [f"Maximum {MAX_REPORT_PHOTOS} photos allowed."]
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        report = create_report_with_photos(
            nagorik=request.user,
            validated_data=serializer.validated_data,
            photos=photos,
        )
        return Response(
            ReportDetailSerializer(report, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["reports"])
class NagorikReportDetailView(generics.RetrieveAPIView):
    """Nagorik can open only their own report."""

    permission_classes = [IsNagorik]
    serializer_class = ReportDetailSerializer
    lookup_field = "id"
    lookup_url_kwarg = "report_id"

    def get_queryset(self):
        return _report_queryset().filter(reporter=self.request.user)


# ---------------------------------------------------------------------------
# Administration
# ---------------------------------------------------------------------------


@extend_schema(tags=["admin"])
class AdminReportInboxView(generics.ListAPIView):
    """
    All reports in the administration user's district.

    Optional query: ?status=pending
    """

    permission_classes = [IsAdministration]
    serializer_class = ReportListSerializer

    def get_queryset(self):
        qs = _report_queryset()
        user = self.request.user
        if not user.is_superuser:
            qs = qs.filter(district_id=user.district_id)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


@extend_schema(tags=["admin"])
class AdminReportDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdministration]
    serializer_class = ReportDetailSerializer
    lookup_field = "id"
    lookup_url_kwarg = "report_id"

    def get_queryset(self):
        qs = _report_queryset()
        user = self.request.user
        if not user.is_superuser:
            qs = qs.filter(district_id=user.district_id)
        return qs


@extend_schema(tags=["admin"])
class AdminStaffListView(generics.ListAPIView):
    """Approved staff in the same district — for the assign dropdown."""

    permission_classes = [IsAdministration]
    serializer_class = StaffBriefSerializer
    pagination_class = None

    def get_queryset(self):
        qs = User.objects.filter(role=User.Role.STAFF, is_approved=True)
        user = self.request.user
        if not user.is_superuser:
            qs = qs.filter(district_id=user.district_id)
        return qs.order_by("full_name", "phone")


@extend_schema(tags=["admin"])
class AdminAssignReportView(APIView):
    """Assign a report to a staff member in the same district."""

    permission_classes = [IsAdministration]

    def post(self, request, report_id):
        report = _admin_get_report(request.user, report_id)
        if report is None:
            return Response(
                {"error": "not_found", "detail": "Report not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AssignReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = serializer.validated_data["staff"]

        report = assign_report_to_staff(
            report=report, staff=staff, admin=request.user
        )
        return Response(ReportDetailSerializer(report, context={"request": request}).data)


@extend_schema(tags=["admin"])
class AdminSetPriorityView(APIView):
    permission_classes = [IsAdministration]

    def patch(self, request, report_id):
        report = _admin_get_report(request.user, report_id)
        if report is None:
            return Response(
                {"error": "not_found", "detail": "Report not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AdminPrioritySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = admin_set_priority(
            report=report,
            admin=request.user,
            priority=serializer.validated_data["priority"],
        )
        return Response(ReportDetailSerializer(report, context={"request": request}).data)


@extend_schema(tags=["admin"])
class AdminRejectReportView(APIView):
    permission_classes = [IsAdministration]

    def post(self, request, report_id):
        report = _admin_get_report(request.user, report_id)
        if report is None:
            return Response(
                {"error": "not_found", "detail": "Report not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        report = admin_reject_report(report=report, admin=request.user)
        return Response(ReportDetailSerializer(report, context={"request": request}).data)


@extend_schema(tags=["admin"])
class AdminDashboardStatsView(APIView):
    """Counts for the administration dashboard (district-scoped)."""

    permission_classes = [IsAdministration]

    def get(self, request):
        qs = Report.objects.all()
        if not request.user.is_superuser:
            qs = qs.filter(district_id=request.user.district_id)

        by_status = list(
            qs.values("status").annotate(count=Count("id")).order_by("status")
        )
        return Response(
            {
                "total": qs.count(),
                "pending": qs.filter(status="pending").count(),
                "assigned": qs.filter(status="assigned").count(),
                "in_progress": qs.filter(status="in_progress").count(),
                "resolved": qs.filter(status="resolved").count(),
                "by_status": by_status,
            }
        )


def _admin_get_report(user, report_id):
    qs = _report_queryset()
    if not user.is_superuser:
        qs = qs.filter(district_id=user.district_id)
    try:
        return qs.get(pk=report_id)
    except Report.DoesNotExist:
        return None


# ---------------------------------------------------------------------------
# Staff
# ---------------------------------------------------------------------------


@extend_schema(tags=["staff"])
class StaffTaskListView(generics.ListAPIView):
    """Tickets assigned to the logged-in staff member."""

    permission_classes = [IsStaffMember]
    serializer_class = ReportListSerializer

    def get_queryset(self):
        qs = _report_queryset().filter(assigned_to=self.request.user)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


@extend_schema(tags=["staff"])
class StaffTaskDetailView(generics.RetrieveAPIView):
    permission_classes = [IsStaffMember]
    serializer_class = ReportDetailSerializer
    lookup_field = "id"
    lookup_url_kwarg = "report_id"

    def get_queryset(self):
        return _report_queryset().filter(assigned_to=self.request.user)


@extend_schema(tags=["staff"])
class StaffUpdateStatusView(APIView):
    """Staff marks assigned work in_progress or resolved."""

    permission_classes = [IsStaffMember]

    def patch(self, request, report_id):
        try:
            report = _report_queryset().get(
                pk=report_id, assigned_to=request.user
            )
        except Report.DoesNotExist:
            return Response(
                {"error": "not_found", "detail": "Task not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = StaffStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = staff_update_status(
            report=report,
            staff=request.user,
            status=serializer.validated_data["status"],
        )
        return Response(ReportDetailSerializer(report, context={"request": request}).data)
