"""Citizen + authority report APIs (MVP)."""
from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reports.models import Category, Report, ReportMedia
from apps.reports.serializers import (
    CategorySerializer,
    ReportCreateSerializer,
    ReportDetailSerializer,
    ReportListSerializer,
    ReportMediaSerializer,
    ReportStatusUpdateSerializer,
)
from apps.reports.services import apply_report_updates
from utils.permissions import IsAdminOrFieldOfficer, IsAuthorityAdmin


@extend_schema(tags=["categories"])
class CategoryListView(generics.ListAPIView):
    """Active categories for one-click reporting UI."""

    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    queryset = Category.objects.filter(is_active=True)


@extend_schema_view(
    get=extend_schema(tags=["reports"]),
    post=extend_schema(tags=["reports"]),
)
class ReportListCreateView(generics.ListCreateAPIView):
    """
    GET: list reports (scoped by role).
    POST: create a report (auth optional — anonymous allowed).
    """

    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Report.objects.select_related("category", "assigned_to")
        user = self.request.user

        if not user.is_authenticated:
            return qs.filter(is_anonymous=False)

        if getattr(user, "is_authority_admin", False) or user.is_superuser:
            return qs
        if getattr(user, "is_field_officer", False):
            return qs.filter(assigned_to=user)

        return qs.filter(Q(reporter=user) | Q(is_anonymous=False)).distinct()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ReportCreateSerializer
        return ReportListSerializer

    def create(self, request, *args, **kwargs):
        serializer = ReportCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        report = serializer.save()
        return Response(
            ReportDetailSerializer(report, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["reports"])
class ReportDetailView(generics.RetrieveAPIView):
    """Single report with media."""

    serializer_class = ReportDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Report.objects.select_related(
        "category", "assigned_to"
    ).prefetch_related("media")
    lookup_field = "id"
    lookup_url_kwarg = "report_id"


@extend_schema(tags=["reports"])
class ReportUpdateView(APIView):
    """Admin / field officer: update status, priority, assignment."""

    permission_classes = [IsAdminOrFieldOfficer]

    def patch(self, request, report_id):
        try:
            report = Report.objects.get(pk=report_id)
        except Report.DoesNotExist:
            return Response(
                {"error": "not_found", "detail": "Report not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ReportStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        is_admin = (
            getattr(request.user, "is_authority_admin", False)
            or request.user.is_superuser
        )

        if "priority" in data and not is_admin:
            return Response(
                {
                    "error": "permission_denied",
                    "detail": "Only admins can change priority.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if "assigned_to" in data and not is_admin:
            return Response(
                {
                    "error": "permission_denied",
                    "detail": "Only admins can assign officers.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        kwargs = {}
        if "status" in data:
            kwargs["status"] = data["status"]
        if "priority" in data:
            kwargs["priority"] = data["priority"]
        if "assigned_to" in data:
            if data["assigned_to"] is None:
                kwargs["clear_assignee"] = True
            else:
                kwargs["assigned_to"] = data["assigned_to"]

        apply_report_updates(report, **kwargs)
        return Response(ReportDetailSerializer(report).data)


@extend_schema(tags=["reports"])
class ReportMediaUploadView(APIView):
    """Upload evidence / before-after media for a report."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, report_id):
        try:
            report = Report.objects.get(pk=report_id)
        except Report.DoesNotExist:
            return Response(
                {"error": "not_found", "detail": "Report not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        file = request.FILES.get("file")
        media_type = request.data.get("media_type", "image")
        kind = request.data.get("kind", ReportMedia.Kind.CITIZEN)

        if not file:
            return Response(
                {"error": "validation_error", "detail": "file is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        media = ReportMedia.objects.create(
            report=report,
            file=file,
            media_type=media_type,
            kind=kind,
            uploaded_by=request.user,
        )
        return Response(
            ReportMediaSerializer(media, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["admin"])
class AdminDashboardStatsView(APIView):
    """Tiny aggregate stats for the authority dashboard (MVP)."""

    permission_classes = [IsAuthorityAdmin]

    def get(self, request):
        by_status = (
            Report.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        by_priority = (
            Report.objects.values("priority")
            .annotate(count=Count("id"))
            .order_by("priority")
        )
        return Response(
            {
                "total": Report.objects.count(),
                "by_status": list(by_status),
                "by_priority": list(by_priority),
            }
        )
