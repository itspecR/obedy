from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("journal", "0004_alter_journalentry_action"),
    ]

    operations = [
        migrations.AlterField(
            model_name="journalentry",
            name="action",
            field=models.CharField(
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
                    ("lunch_deleted", "Удалён обед"),
                    ("lunches_reset", "Обеды сброшены"),
                    ("rules_changed", "Изменены правила обеда"),
                    ("network_added", "Добавлен адрес доступа"),
                    ("network_removed", "Удалён адрес доступа"),
                    ("private_networks_changed", "Изменён доступ из локальной сети"),
                    ("directory_changed", "Изменены настройки домена"),
                    ("directory_checked", "Проверка связи с доменом"),
                    ("directory_synced", "Синхронизация с доменом"),
                    ("database_changed", "Изменено подключение к базе"),
                    ("backup_done", "Резервная копия базы"),
                ],
                max_length=32,
            ),
        ),
    ]
