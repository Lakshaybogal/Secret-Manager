from django.db import models
from django.utils import timezone
from uuid import uuid4


class User(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("admin", "Admin"),
        ("moderator", "Moderator"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    password = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100, null=True, blank=True)
    lastname = models.CharField(max_length=100, null=True, blank=True)
    contact = models.CharField(
        max_length=15, null=True, blank=True
    )  # Consider increasing the max_length
    lastLogin = models.DateTimeField(default=timezone.now)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.email}) ({self.role})"
