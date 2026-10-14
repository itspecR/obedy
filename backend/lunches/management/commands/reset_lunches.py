from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from journal.entries import Row, record_server
from journal.models import Action
from lunches.models import Lunch

NOT_CONFIRMED = "Ничего не удалено. Запустите sudo ./scripts/reset-stats.sh — он сделает резервную копию и спросит подтверждение"
DELETED_LABEL = "Удалено обедов"


class Command(BaseCommand):
    help = "Удаляет все обеды за всё время. Сотрудники, правила, настройки и журнал остаются"

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="подтвердить удаление")

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["yes"]:
            raise CommandError(NOT_CONFIRMED)
        deleted, _ = Lunch.objects.all().delete()
        record_server(Action.LUNCHES_RESET, rows=[Row(DELETED_LABEL, after=str(deleted))])
        self.stdout.write(f"Удалено обедов: {deleted}")
