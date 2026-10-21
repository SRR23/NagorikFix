"""Auth + district routes (mounted under /api/)."""
from django.conf import settings
from django.urls import path

from apps.accounts.views import (
    ApproveUserView,
    DistrictListView,
    LoginView,
    LogoutView,
    MeView,
    PendingUsersListView,
    RefreshView,
    RegisterView,
    SwaggerDevTokenView,
)

app_name = "accounts"

urlpatterns = [
    path("districts/", DistrictListView.as_view(), name="district-list"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", RefreshView.as_view(), name="refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
    path(
        "auth/pending-users/",
        PendingUsersListView.as_view(),
        name="pending-users",
    ),
    path(
        "auth/approve/<int:user_id>/",
        ApproveUserView.as_view(),
        name="approve-user",
    ),
]

if settings.DEBUG:
    urlpatterns.append(
        path(
            "auth/swagger-token/",
            SwaggerDevTokenView.as_view(),
            name="swagger-dev-token",
        )
    )
