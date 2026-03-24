import json

import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError

from apps.accounts.factories import FabUserFactory, LabStaffFactory, UserProfileFactory


@pytest.mark.django_db
class TestUserProfile:
    def test_create_user_profile(self):
        """UserProfile is auto-created by signal; fields can be updated."""
        from apps.accounts.models import Role, UserProfile

        user = User.objects.create_user(username="fab01", password="pass")
        profile, _ = UserProfile.objects.update_or_create(
            user=user,
            defaults={"role": Role.FAB_USER, "department": "廠區 A"},
        )

        assert profile.user == user
        assert profile.role == Role.FAB_USER
        assert profile.department == "廠區 A"
        assert profile.created_at is not None
        assert profile.updated_at is not None

    def test_one_to_one_relationship(self):
        """UserProfile has a OneToOne relation with User; duplicates are rejected."""
        from apps.accounts.models import Role, UserProfile

        user = User.objects.create_user(username="lab01", password="pass")
        # Signal already creates a profile; a second explicit create must fail.
        with pytest.raises(IntegrityError):
            UserProfile.objects.create(user=user, role=Role.LAB_MANAGER)

    def test_access_profile_from_user(self):
        """UserProfile is accessible via the reverse relation user.profile."""
        from apps.accounts.models import Role

        user = User.objects.create_user(username="mgr01", password="pass")
        user.profile.role = Role.LAB_MANAGER
        user.profile.save()

        assert user.profile.role == Role.LAB_MANAGER

    def test_department_optional(self):
        """department field defaults to an empty string."""
        user = User.objects.create_user(username="nodev", password="pass")

        assert user.profile.department == ""

    def test_db_table_name(self):
        """Database table name is user_profile."""
        from apps.accounts.models import UserProfile

        assert UserProfile._meta.db_table == "user_profile"


@pytest.mark.django_db
class TestUserProfileSignal:
    """Tests for the post_save signal that auto-creates UserProfile."""

    def test_profile_auto_created_on_user_creation(self):
        """UserProfile is automatically created when a User is created."""
        from apps.accounts.models import Role

        user = User.objects.create_user(username="signaluser", password="pass")

        assert hasattr(user, "profile")
        assert user.profile.role == Role.FAB_USER

    def test_signal_does_not_create_duplicate_profile(self):
        """Signal uses get_or_create; no duplicate profile is created."""
        user = User.objects.create_user(username="signaldup", password="pass")

        from apps.accounts.models import UserProfile

        assert UserProfile.objects.filter(user=user).count() == 1

    def test_signal_not_fired_on_user_update(self):
        """Saving an existing User does not create or overwrite the profile."""
        from apps.accounts.models import Role

        user = User.objects.create_user(username="signalupdate", password="pass")
        user.profile.role = Role.LAB_MANAGER
        user.profile.save()

        user.first_name = "Updated"
        user.save()

        user.profile.refresh_from_db()
        assert user.profile.role == Role.LAB_MANAGER


@pytest.mark.django_db
class TestRoleChoices:
    def test_role_values(self):
        """Role contains the three expected values."""
        from apps.accounts.models import Role

        assert Role.FAB_USER == "fab_user"
        assert Role.LAB_STAFF == "lab_staff"
        assert Role.LAB_MANAGER == "lab_manager"

    def test_all_roles_are_valid_choices(self):
        """All Role values are valid choices on the UserProfile model."""
        from apps.accounts.models import UserProfile

        valid_values = {choice[0] for choice in UserProfile.role.field.choices}
        assert "fab_user" in valid_values
        assert "lab_staff" in valid_values
        assert "lab_manager" in valid_values


# ---------------------------------------------------------------------------
# Auth API tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAuthLoginAPI:
    """Tests for POST /api/auth/login endpoint."""

    def test_login_success_returns_200_and_user_data(self, client):
        """Login with valid credentials returns 200 and user info."""
        profile = FabUserFactory(department="廠區 A")

        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                {"username": profile.user.username, "password": "testpass123"}
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == profile.user.username
        assert data["role"] == "fab_user"
        assert data["department"] == "廠區 A"

    def test_login_wrong_password_returns_401(self, client):
        """Login with wrong password returns 401."""
        profile = UserProfileFactory()

        response = client.post(
            "/api/auth/login",
            data=json.dumps({"username": profile.user.username, "password": "wrong"}),
            content_type="application/json",
        )

        assert response.status_code == 401

    def test_login_nonexistent_user_returns_401(self, client):
        """Login with a nonexistent username returns 401."""
        response = client.post(
            "/api/auth/login",
            data=json.dumps({"username": "nobody", "password": "pass123"}),
            content_type="application/json",
        )

        assert response.status_code == 401

    def test_login_no_profile_returns_same_401_as_wrong_password(self, client):
        """Valid credentials but no UserProfile return 401 with identical message.

        Ensures no information is leaked about whether the account exists.
        Profile is deleted after signal creation to simulate the edge case.
        """
        user = User.objects.create_user(username="noprofile", password="pass123")
        user.profile.delete()  # Remove the auto-created profile.

        wrong_pw_response = client.post(
            "/api/auth/login",
            data=json.dumps({"username": user.username, "password": "wrong"}),
            content_type="application/json",
        )
        no_profile_response = client.post(
            "/api/auth/login",
            data=json.dumps({"username": user.username, "password": "pass123"}),
            content_type="application/json",
        )

        assert wrong_pw_response.status_code == 401
        assert no_profile_response.status_code == 401
        assert (
            wrong_pw_response.json()["detail"] == no_profile_response.json()["detail"]
        )


@pytest.mark.django_db
class TestAuthLogoutAPI:
    """Tests for POST /api/auth/logout endpoint."""

    def test_logout_returns_200(self, client):
        """Logout returns 200 and terminates the session."""
        profile = UserProfileFactory()
        client.force_login(profile.user)

        response = client.post("/api/auth/logout")

        assert response.status_code == 200

    def test_logout_returns_401_when_unauthenticated(self, client):
        """Unauthenticated logout attempt returns 401."""
        response = client.post("/api/auth/logout")

        assert response.status_code == 401

    def test_logout_destroys_session(self, client):
        """After logout, GET /me returns 401."""
        profile = UserProfileFactory()
        client.force_login(profile.user)
        client.post("/api/auth/logout")

        response = client.get("/api/auth/me")

        assert response.status_code == 401


@pytest.mark.django_db
class TestAuthMeAPI:
    """Tests for GET /api/auth/me endpoint."""

    def test_me_returns_user_info_when_authenticated(self, client):
        """GET /me returns current user info when authenticated."""
        profile = LabStaffFactory(department="Lab A")
        client.force_login(profile.user)

        response = client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == profile.user.username
        assert data["role"] == "lab_staff"
        assert data["department"] == "Lab A"

    def test_me_returns_401_when_unauthenticated(self, client):
        """GET /me returns 401 when no user is authenticated."""
        response = client.get("/api/auth/me")

        assert response.status_code == 401
