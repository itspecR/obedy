from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from accounts.first_admin import existing_admin
from config.setup_code import forget_code


class Command(BaseCommand):
    help = "Применяет миграции, если база подключена (вызывается при запуске контейнера)"

    def handle(self, *args, **options):
        if not settings.DATABASE_CONFIGURED:
            return
        call_command("migrate", interactive=False)
        if existing_admin() is not None:
            forget_code(settings.SETUP_CODE_FILE)
