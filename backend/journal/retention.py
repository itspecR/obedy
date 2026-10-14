from datetime import timedelta

from journal.models import JournalEntry

RETENTION_DAYS = 3 * 365 + 1


def delete_expired_entries(now):
    deleted, _ = JournalEntry.objects.filter(created_at__lt=now - timedelta(days=RETENTION_DAYS)).delete()
    return deleted
