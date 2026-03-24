"""Django Ninja router for authentication endpoints."""

from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.http import HttpRequest
from ninja import Router
from ninja.security import django_auth

from apps.accounts.models import UserProfile
from apps.accounts.schemas import ErrorOut, LoginIn, UserOut

router = Router(tags=["Auth"])

# Single constant prevents info leakage by returning the same message
# for both wrong credentials and valid credentials without a profile.
_INVALID_CREDENTIALS = "Invalid credentials"


@router.post("/login", response={200: UserOut, 401: ErrorOut}, auth=None)
def login_view(request: HttpRequest, payload: LoginIn):
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
    return 200, UserOut.to_dict(user, profile)


@router.post("/logout", response={200: ErrorOut, 401: ErrorOut}, auth=django_auth)
def logout_view(request: HttpRequest):
    """End the current user session. Requires authentication."""
    django_logout(request)
    return 200, {"detail": "Logged out"}


@router.get("/me", response={200: UserOut, 401: ErrorOut}, auth=django_auth)
def me_view(request: HttpRequest):
    """Return the currently authenticated user's information.

    Unauthenticated requests are rejected by django_auth before reaching
    this function.
    """
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return 401, {"detail": _INVALID_CREDENTIALS}
    return 200, UserOut.to_dict(request.user, profile)
