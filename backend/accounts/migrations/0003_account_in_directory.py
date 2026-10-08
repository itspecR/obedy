from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_account_department_account_external_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="in_directory",
            field=models.BooleanField(default=True),
        ),
    ]
