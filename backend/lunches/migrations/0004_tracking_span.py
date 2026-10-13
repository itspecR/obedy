import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone

LUNCHLESS_ROLE = "admin"
DOMAIN_SOURCE = "domain"


def tracked_now(account):
    present = account.source != DOMAIN_SOURCE or account.in_directory
    return account.is_active and present and account.track_lunch and account.role != LUNCHLESS_ROLE


def open_spans(apps, schema_editor):
    Account = apps.get_model("accounts", "Account")
    TrackingSpan = apps.get_model("lunches", "TrackingSpan")
    for account in Account.objects.all():
        if tracked_now(account):
            TrackingSpan.objects.create(account=account, started_on=timezone.localdate(account.created_at))


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_remove_department_position"),
        ("lunches", "0003_lunchrules_rabbit_enabled"),
    ]

    operations = [
        migrations.CreateModel(
            name="TrackingSpan",
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
                ("started_on", models.DateField()),
                ("ended_on", models.DateField(blank=True, null=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="tracking_spans",
                        to="accounts.account",
                    ),
                ),
            ],
        ),
        migrations.RunPython(open_spans, migrations.RunPython.noop),
    ]
