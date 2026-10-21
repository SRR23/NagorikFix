"""Auth + district endpoints."""
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.models import District
from apps.accounts.serializers import (
    DistrictSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)
from utils.permissions import IsAdministration

User = get_user_model()


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


@extend_schema(tags=["districts"])
class DistrictListView(generics.ListAPIView):
    """Active districts for the signup dropdown."""

    serializer_class = DistrictSerializer
    permission_classes = [permissions.AllowAny]
    queryset = District.objects.filter(is_active=True)
    pagination_class = None


@extend_schema(tags=["auth"])
class RegisterView(APIView):
    """
    Sign up as nagorik / staff / administration.

    Returns JWT only when the account is approved (nagorik by default).
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        payload = {
            "user": UserSerializer(user).data,
            "message": (
                "Registration successful."
                if user.is_approved
                else "Registration successful. Waiting for administration approval."
            ),
        }
        if user.can_use_app:
            payload["tokens"] = _tokens_for_user(user)

        return Response(payload, status=status.HTTP_201_CREATED)


@extend_schema(tags=["auth"])
class LoginView(APIView):
    """Phone / password login → JWT (approved accounts only)."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data["phone"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {
                    "error": "authentication_failed",
                    "detail": "Invalid phone or password.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.can_use_app:
            return Response(
                {
                    "error": "account_pending_approval",
                    "detail": "Your account is waiting for administration approval.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": _tokens_for_user(user),
            }
        )


@extend_schema(tags=["auth"])
class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(tags=["auth"])
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"error": "validation_error", "detail": "refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except Exception:
            return Response(
                {"error": "validation_error", "detail": "Invalid refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(post=extend_schema(tags=["auth"]))
class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=["auth"])
class PendingUsersListView(generics.ListAPIView):
    """Administration: list staff/admin accounts waiting for approval."""

    serializer_class = UserSerializer
    permission_classes = [IsAdministration]

    def get_queryset(self):
        return User.objects.filter(
            is_approved=False,
            role__in=[User.Role.STAFF, User.Role.ADMINISTRATION],
        ).select_related("district")


@extend_schema(tags=["auth"])
class ApproveUserView(APIView):
    """Administration (or superuser) approves a pending staff/admin account."""

    permission_classes = [IsAdministration]

    def post(self, request, user_id):
        try:
            target = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "not_found", "detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if target.role == User.Role.NAGORIK:
            return Response(
                {
                    "error": "validation_error",
                    "detail": "Nagorik accounts do not need approval.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        target.is_approved = True
        target.save(update_fields=["is_approved"])
        return Response(UserSerializer(target).data)


@extend_schema(exclude=True)
class SwaggerDevTokenView(APIView):
    """DEBUG-only: issue JWT for local Swagger auto-auth."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        if not settings.DEBUG:
            return Response(status=status.HTTP_404_NOT_FOUND)

        username = getattr(settings, "SWAGGER_SUPERUSER_USERNAME", "swagger")
        password = getattr(settings, "SWAGGER_SUPERUSER_PASSWORD", None)
        if not password:
            return Response(
                {"detail": "SWAGGER_SUPERUSER_PASSWORD is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        phone = "01700000000"
        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={
                "username": phone,
                "full_name": username,
                "role": User.Role.ADMINISTRATION,
                "is_staff": True,
                "is_superuser": True,
                "is_approved": True,
            },
        )
        if created or not user.check_password(password):
            user.set_password(password)
            user.is_approved = True
            user.is_superuser = True
            user.is_staff = True
            user.save()

        return Response(
            {
                "access": _tokens_for_user(user)["access"],
                "username": user.phone,
            }
        )
