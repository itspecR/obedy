from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lunches", "0006_absence"),
    ]

    operations = [
        migrations.AddField(
            model_name="lunchrules",
            name="missing_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="lunchrules",
            name="missing_since",
            field=models.DateField(blank=True, null=True),
        ),
    ]
