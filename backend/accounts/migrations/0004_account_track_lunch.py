from django.db import migrations, models

UNTRACKED_ROLES = ("hr", "admin")


def untrack_staff_roles(apps, schema_editor):
    Account = apps.get_model("accounts", "Account")
    Account.objects.filter(role__in=UNTRACKED_ROLES).update(track_lunch=False)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_account_in_directory"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="track_lunch",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(untrack_staff_roles, migrations.RunPython.noop),
    ]
