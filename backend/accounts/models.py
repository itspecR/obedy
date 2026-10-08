from django.db import models


class Role(models.TextChoices):
    EMPLOYEE = "employee", "Сотрудник"
    HR = "hr", "HR"
    ADMIN = "admin", "Администратор"


class Source(models.TextChoices):
    LOCAL = "local", "Локальная"
    DOMAIN = "domain", "Домен"


class Account(models.Model):
    login = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.LOCAL)
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.EMPLOYEE)
    password_hash = models.CharField(max_length=255, blank=True)
    must_change_password = models.BooleanField(default=False)
    weak_password = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    failed_count = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)


class Session(models.Model):
    token_hash = models.CharField(max_length=64, unique=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="sessions")
    account_version = models.PositiveIntegerField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class KnownDevice(models.Model):
    token_hash = models.CharField(max_length=64, unique=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="known_devices")
    failed_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
