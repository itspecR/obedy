from django.db import models

SETTINGS_ID = 1
DEFAULT_SESSION_DAYS = 30


class Mode(models.TextChoices):
    LDAPS = "ldaps", "LDAPS"
    STARTTLS = "starttls", "StartTLS"
    PLAIN = "plain", "LDAP без шифрования"


class DirectorySettings(models.Model):
    enabled = models.BooleanField(default=False)
    servers = models.CharField(max_length=500, blank=True)
    mode = models.CharField(max_length=16, choices=Mode.choices, default=Mode.LDAPS)
    port = models.PositiveIntegerField(null=True, blank=True)
    ca_certificate = models.TextField(blank=True)
    bind_user = models.CharField(max_length=255, blank=True)
    bind_password = models.TextField(blank=True)
    base_dn = models.CharField(max_length=500, blank=True)
    group_dn = models.CharField(max_length=500, blank=True)
    session_days = models.PositiveSmallIntegerField(default=DEFAULT_SESSION_DAYS)
    updated_at = models.DateTimeField(auto_now=True)


class SyncStatus(models.TextChoices):
    DONE = "done", "Выполнена"
    SKIPPED = "skipped", "Не выполнялась"
    GUARDED = "guarded", "Остановлена защитой"
    FAILED = "failed", "Ошибка"


class SyncReport(models.Model):
    finished_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=SyncStatus.choices)
    message = models.CharField(max_length=1000)
    created = models.PositiveIntegerField(default=0)
    updated = models.PositiveIntegerField(default=0)
    deactivated = models.PositiveIntegerField(default=0)
    skipped = models.PositiveIntegerField(default=0)
