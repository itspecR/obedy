from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Применяет миграции, если база подключена (вызывается при запуске контейнера)"

    def handle(self, *args, **options):
        if settings.DATABASE_CONFIGURED:
            call_command("migrate", interactive=False)
