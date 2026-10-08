from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.devices import delete_expired_devices
from accounts.sessions import delete_expired_sessions


class Command(BaseCommand):
    help = "Удаляет истёкшие сессии и просроченные знакомые устройства"

    def handle(self, *args, **options):
        now = timezone.now()
        sessions = delete_expired_sessions(now)
        devices = delete_expired_devices(now)
        self.stdout.write(f"Удалено сессий: {sessions}, устройств: {devices}")
