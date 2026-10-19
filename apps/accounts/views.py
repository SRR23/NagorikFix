"""Auth endpoints: register, login, refresh, logout, me."""
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


@extend_schema(tags=["auth"])
class RegisterView(generics.CreateAPIView):
    """Public citizen registration. Always creates role=citizen."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": _tokens_for_user(user),
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["auth"])
class LoginView(APIView):
    """Email / password login → JWT pair."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # AUTH_USER_MODEL uses email as USERNAME_FIELD.
        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"error": "authentication_failed", "detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": _tokens_for_user(user),
            }
        )


@extend_schema(tags=["auth"])
class MeView(generics.RetrieveAPIView):
    """Current authenticated user profile."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(tags=["auth"])
class LogoutView(APIView):
    """Blacklist the refresh token (requires token_blacklist app)."""

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


@extend_schema_view(
    post=extend_schema(tags=["auth"]),
)
class RefreshView(TokenRefreshView):
    """Standard SimpleJWT refresh."""

    permission_classes = [permissions.AllowAny]


@extend_schema(exclude=True)
class SwaggerDevTokenView(APIView):
    """
    DEBUG-only helper: issue a JWT for a local staff user so Swagger
    can auto-authorize. Never enable in production.
    """

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

        user, created = User.objects.get_or_create(
            email=f"{username}@localhost",
            defaults={
                "username": username,
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created or not user.check_password(password):
            user.set_password(password)
            user.save(update_fields=["password"])

        tokens = _tokens_for_user(user)
        return Response(
            {
                "access": tokens["access"],
                "username": user.username,
            }
        )
