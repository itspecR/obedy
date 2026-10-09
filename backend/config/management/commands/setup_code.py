from django.conf import settings
from django.core.management.base import BaseCommand

from config.setup_code import issue_code


class Command(BaseCommand):
    help = "Выдаёт одноразовый код для подключения базы на сайте"

    def handle(self, *args, **options):
        self.stdout.write(f"Код настройки: {issue_code(settings.SETUP_CODE_FILE)}")
