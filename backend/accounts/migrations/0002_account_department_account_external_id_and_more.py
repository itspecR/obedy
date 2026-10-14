
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="department",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="account",
            name="external_id",
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="account",
            name="position",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
