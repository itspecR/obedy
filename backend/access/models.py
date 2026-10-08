from django.db import models

POLICY_ID = 1


class AccessPolicy(models.Model):
    allow_private_networks = models.BooleanField(default=True)


class AllowedNetwork(models.Model):
    network = models.CharField(max_length=64, unique=True)
    note = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
