
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("login", models.CharField(max_length=150, unique=True)),
                ("full_name", models.CharField(blank=True, max_length=255)),
                (
                    "source",
                    models.CharField(
                        choices=[("local", "Локальная"), ("domain", "Домен")],
                        default="local",
                        max_length=16,
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("employee", "Сотрудник"),
                            ("hr", "HR"),
                            ("admin", "Администратор"),
                        ],
                        default="employee",
                        max_length=16,
                    ),
                ),
                ("password_hash", models.CharField(blank=True, max_length=255)),
                ("must_change_password", models.BooleanField(default=False)),
                ("weak_password", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("last_login_at", models.DateTimeField(blank=True, null=True)),
                ("failed_count", models.PositiveIntegerField(default=0)),
                ("locked_until", models.DateTimeField(blank=True, null=True)),
                ("version", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="KnownDevice",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("failed_count", models.PositiveIntegerField(default=0)),
                ("expires_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="known_devices",
                        to="accounts.account",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Session",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("account_version", models.PositiveIntegerField()),
                ("expires_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sessions",
                        to="accounts.account",
                    ),
                ),
            ],
        ),
    ]
