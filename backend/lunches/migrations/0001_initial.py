import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0004_account_track_lunch"),
    ]

    operations = [
        migrations.CreateModel(
            name="LunchRules",
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
                ("limit_minutes", models.PositiveSmallIntegerField(default=45)),
                ("workdays", models.CharField(default="12345", max_length=7)),
                ("day_end", models.TimeField(default=datetime.time(18, 0))),
                ("window_enabled", models.BooleanField(default=False)),
                ("window_start", models.TimeField(default=datetime.time(12, 0))),
                ("window_end", models.TimeField(default=datetime.time(15, 0))),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Lunch",
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
                ("day", models.DateField()),
                ("started_at", models.DateTimeField()),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("limit_minutes", models.PositiveSmallIntegerField()),
                ("auto_closed", models.BooleanField(default=False)),
                ("corrected_at", models.DateTimeField(blank=True, null=True)),
                ("correction_reason", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lunches",
                        to="accounts.account",
                    ),
                ),
                (
                    "corrected_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="accounts.account",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["day"], name="lunches_lun_day_86dd24_idx")
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("account", "day"), name="one_lunch_per_day"
                    )
                ],
            },
        ),
    ]
