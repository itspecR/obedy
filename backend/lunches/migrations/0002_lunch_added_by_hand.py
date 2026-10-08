from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lunches", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="lunch",
            name="added_by_hand",
            field=models.BooleanField(default=False),
        ),
    ]
