from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from config.connection_store import forget_connection


class Command(BaseCommand):
    help = "Забывает подключение к базе и выдаёт новый код настройки"

    def handle(self, *args, **options):
        forget_connection(settings.DB_CONFIG_FILE)
        call_command("setup_code", stdout=self.stdout)
