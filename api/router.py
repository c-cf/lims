"""Main NinjaAPI router for the LIMS backend."""

from ninja import NinjaAPI

from apps.accounts.api import router as auth_router

api = NinjaAPI(
    title="LIMS API",
    version="1.0.0",
    description="Laboratory Information Management System API",
)

api.add_router("/auth/", auth_router)


@api.get("/health", tags=["System"])
def health_check(request):
    """Return the health status of the API."""
    return {"status": "ok"}
