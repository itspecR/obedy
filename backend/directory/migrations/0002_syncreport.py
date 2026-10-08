from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("directory", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SyncReport",
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
                ("finished_at", models.DateTimeField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("done", "Выполнена"),
                            ("skipped", "Не выполнялась"),
                            ("guarded", "Остановлена защитой"),
                            ("failed", "Ошибка"),
                        ],
                        max_length=16,
                    ),
                ),
                ("message", models.CharField(max_length=1000)),
                ("created", models.PositiveIntegerField(default=0)),
                ("updated", models.PositiveIntegerField(default=0)),
                ("deactivated", models.PositiveIntegerField(default=0)),
                ("skipped", models.PositiveIntegerField(default=0)),
            ],
        ),
    ]
