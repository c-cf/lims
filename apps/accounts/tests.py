import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError


@pytest.mark.django_db
class TestUserProfile:
    def test_create_user_profile(self):
        """UserProfile can be created and associated with a User."""
        from apps.accounts.models import Role, UserProfile

        user = User.objects.create_user(username="fab01", password="pass")
        profile = UserProfile.objects.create(
            user=user,
            role=Role.FAB_USER,
            department="廠區 A",
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
        UserProfile.objects.create(user=user, role=Role.LAB_STAFF)

        with pytest.raises(IntegrityError):
            UserProfile.objects.create(user=user, role=Role.LAB_MANAGER)

    def test_access_profile_from_user(self):
        """UserProfile is accessible via the reverse relation user.profile."""
        from apps.accounts.models import Role, UserProfile

        user = User.objects.create_user(username="mgr01", password="pass")
        UserProfile.objects.create(user=user, role=Role.LAB_MANAGER)

        assert user.profile.role == Role.LAB_MANAGER

    def test_department_optional(self):
        """department field defaults to an empty string."""
        from apps.accounts.models import Role, UserProfile

        user = User.objects.create_user(username="nodev", password="pass")
        profile = UserProfile.objects.create(user=user, role=Role.LAB_STAFF)

        assert profile.department == ""

    def test_db_table_name(self):
        """Database table name is user_profile."""
        from apps.accounts.models import UserProfile

        assert UserProfile._meta.db_table == "user_profile"


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
