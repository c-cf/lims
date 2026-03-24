"""Django Ninja router for authentication endpoints."""

from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.models import User
from ninja import Router, Schema
from ninja.security import django_auth

from apps.accounts.models import UserProfile

router = Router(tags=["Auth"])

# Single constant prevents info leakage by returning the same message
# for both wrong credentials and valid credentials without a profile.
_INVALID_CREDENTIALS = "Invalid credentials"


class LoginIn(Schema):
    """Input schema for the login endpoint."""

    username: str
    password: str


class UserOut(Schema):
    """Output schema representing an authenticated user with role information."""

    id: int
    username: str
    role: str
    department: str


class ErrorOut(Schema):
    """Output schema for generic detail messages (errors and confirmations)."""

    detail: str


def _build_user_out(user: "User", profile: UserProfile) -> dict:
    """Return a dict matching UserOut fields from a User and its UserProfile."""
    return {
        "id": user.pk,
        "username": user.username,
        "role": profile.role,
        "department": profile.department,
    }


@router.post("/login", response={200: UserOut, 401: ErrorOut}, auth=None)
def login_view(request, payload: LoginIn):
    """Authenticate a user and create a session.

    Returns user information on success, or 401 on invalid credentials.
    The same error message is used regardless of whether authentication
    failed or the user has no profile, to prevent information leakage.
    """
    user = authenticate(request, username=payload.username, password=payload.password)
    if user is None:
        return 401, {"detail": _INVALID_CREDENTIALS}
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        return 401, {"detail": _INVALID_CREDENTIALS}
    django_login(request, user)
    return 200, _build_user_out(user, profile)


@router.post("/logout", response={200: ErrorOut, 401: ErrorOut}, auth=django_auth)
def logout_view(request):
    """End the current user session. Requires authentication."""
    django_logout(request)
    return 200, {"detail": "Logged out"}


@router.get("/me", response={200: UserOut, 401: ErrorOut}, auth=django_auth)
def me_view(request):
    """Return the currently authenticated user's information.

    Unauthenticated requests are rejected by django_auth before reaching
    this function.
    """
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return 401, {"detail": _INVALID_CREDENTIALS}
    return 200, _build_user_out(request.user, profile)
