from django.core.management.base import BaseCommand

from journal.entries import Row, record_server
from journal.models import Action

FILE_LABEL = "Файл"


class Command(BaseCommand):
    help = "Отмечает в журнале успешную резервную копию базы (вызывает scripts/backup.sh)"

    def add_arguments(self, parser):
        parser.add_argument("file")

    def handle(self, *args, **options):
        record_server(Action.BACKUP_DONE, rows=[Row(FILE_LABEL, after=options["file"])])
