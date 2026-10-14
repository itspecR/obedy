
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DirectorySettings",
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
                ("enabled", models.BooleanField(default=False)),
                ("servers", models.CharField(blank=True, max_length=500)),
                (
                    "mode",
                    models.CharField(
                        choices=[
                            ("ldaps", "LDAPS"),
                            ("starttls", "StartTLS"),
                            ("plain", "LDAP без шифрования"),
                        ],
                        default="ldaps",
                        max_length=16,
                    ),
                ),
                ("port", models.PositiveIntegerField(blank=True, null=True)),
                ("ca_certificate", models.TextField(blank=True)),
                ("bind_user", models.CharField(blank=True, max_length=255)),
                ("bind_password", models.TextField(blank=True)),
                ("base_dn", models.CharField(blank=True, max_length=500)),
                ("group_dn", models.CharField(blank=True, max_length=500)),
                ("session_days", models.PositiveSmallIntegerField(default=30)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
