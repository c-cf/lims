from django.contrib.auth.models import User
from django.db import models


class Role(models.TextChoices):
    FAB_USER = "fab_user", "廠區使用者"
    LAB_STAFF = "lab_staff", "實驗室人員"
    LAB_MANAGER = "lab_manager", "實驗室主管"


class UserProfile(models.Model):
    """Extends Django User with role and department fields."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=Role.choices)
    department = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profile"

    def __str__(self):
        return f"{self.user.username} ({self.role})"
