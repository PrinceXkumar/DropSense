from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = "admin"
    ROLE_MENTOR = "mentor"
    ROLE_PARENT = "parent"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_MENTOR, "Mentor"),
        (ROLE_PARENT, "Parent"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_PARENT)

    def natural_display(self) -> str:
        """Human-readable label for admin dropdowns and FK widgets."""
        username = self.get_username()
        full = (self.get_full_name() or "").strip()
        if full:
            return f"{full} ({username})"
        return username or f"user #{self.pk}"

    def __str__(self) -> str:
        return self.natural_display()

    def is_admin(self) -> bool:
        return self.role == self.ROLE_ADMIN or self.is_superuser

    def is_mentor(self) -> bool:
        return self.role == self.ROLE_MENTOR

    def is_parent(self) -> bool:
        return self.role == self.ROLE_PARENT

