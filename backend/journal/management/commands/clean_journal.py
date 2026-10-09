from django.core.management.base import BaseCommand
from django.utils import timezone

from journal.retention import RETENTION_DAYS, delete_expired_entries


class Command(BaseCommand):
    help = f"Удаляет записи журнала действий старше {RETENTION_DAYS} дней"

    def handle(self, *args, **options):
        deleted = delete_expired_entries(timezone.now())
        self.stdout.write(f"Удалено записей журнала: {deleted}")
