from django.db import models
from secret_manager.apps.users.models import User
from uuid import uuid4
from secret_manager.utili import unique_id


class EnvSecret(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    key = models.TextField()

    def __str__(self):
        return self.key


class Env(models.Model):
    id = models.CharField(
        max_length=18, primary_key=True, default=unique_id, editable=False
    )
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=1000)
    user = models.ForeignKey(User, to_field="email", on_delete=models.CASCADE)
    key_id = models.ForeignKey(EnvSecret, to_field="id", on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    access_password = models.CharField(max_length=100, default="")
    api_requests = models.IntegerField(default=1000)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    # add api access passwird
    class Meta:
        unique_together = ("name", "user")

    def __str__(self):
        return f"{self.name} ({self.value})"
