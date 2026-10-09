import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0005_remove_department_position"),
    ]

    operations = [
        migrations.CreateModel(
            name="JournalEntry",
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("login", "Вход"),
                            ("login_failed", "Неудачный вход"),
                            ("logout", "Выход"),
                            ("password_changed", "Сменил свой пароль"),
                            ("role_changed", "Изменена роль"),
                            ("track_lunch_changed", "Изменён учёт обеда"),
                            ("blocked", "Заблокирован"),
                            ("unblocked", "Разблокирован"),
                            ("account_created", "Создана учётная запись"),
                            ("profile_changed", "Изменено ФИО"),
                            ("password_issued", "Выдан временный пароль"),
                            ("lunch_corrected", "Исправлен обед"),
                            ("lunch_added", "Добавлен обед"),
                            ("rules_changed", "Изменены правила обеда"),
                            ("network_added", "Добавлен адрес доступа"),
                            ("network_removed", "Удалён адрес доступа"),
                            (
                                "private_networks_changed",
                                "Изменён доступ из локальной сети",
                            ),
                            ("directory_changed", "Изменены настройки домена"),
                            ("directory_checked", "Проверка связи с доменом"),
                            ("directory_synced", "Синхронизация с доменом"),
                        ],
                        max_length=32,
                    ),
                ),
                ("address", models.CharField(blank=True, max_length=45)),
                ("details", models.JSONField(default=list)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="accounts.account",
                    ),
                ),
                (
                    "target",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="accounts.account",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["created_at"], name="journal_jou_created_41a2c3_idx"
                    ),
                    models.Index(
                        fields=["action", "created_at"],
                        name="journal_jou_action_0af6ce_idx",
                    ),
                ],
            },
        ),
    ]
