from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from directory.models import SyncStatus
from directory.sync import SyncBusy, run_sync

FAILED_STATUSES = {SyncStatus.FAILED, SyncStatus.GUARDED}


class Command(BaseCommand):
    help = "Синхронизирует сотрудников с Active Directory"

    def handle(self, *args, **options):
        try:
            result = run_sync(timezone.now())
        except SyncBusy:
            self.stdout.write("Синхронизация уже идёт")
            return
        if result.status in FAILED_STATUSES:
            raise CommandError(result.message)
        self.stdout.write(result.message)
