from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lunches", "0004_tracking_span"),
    ]

    operations = [
        migrations.CreateModel(
            name="CalendarDay",
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
                ("day", models.DateField(unique=True)),
                ("working", models.BooleanField()),
            ],
        ),
    ]
