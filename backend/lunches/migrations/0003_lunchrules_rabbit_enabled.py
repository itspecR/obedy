from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lunches", "0002_lunch_added_by_hand"),
    ]

    operations = [
        migrations.AddField(
            model_name="lunchrules",
            name="rabbit_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
