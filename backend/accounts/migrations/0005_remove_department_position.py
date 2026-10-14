from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_account_track_lunch"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="account",
            name="department",
        ),
        migrations.RemoveField(
            model_name="account",
            name="position",
        ),
    ]
