import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_remove_department_position"),
        ("lunches", "0005_calendar_day"),
    ]

    operations = [
        migrations.CreateModel(
            name="Absence",
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
                ("first", models.DateField()),
                ("last", models.DateField()),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("vacation", "Отпуск"),
                            ("sick", "Больничный"),
                            ("other", "Другое"),
                        ],
                        max_length=16,
                    ),
                ),
                ("note", models.CharField(blank=True, max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="absences",
                        to="accounts.account",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["first", "last"], name="lunches_abs_first_096c7d_idx"
                    )
                ],
            },
        ),
    ]
