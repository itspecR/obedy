from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.lunch_policy import tracks_lunch_by_default
from accounts.models import Account, Role, Source
from accounts.names import normalize_login
from accounts.passwords import hash_password
from accounts.temporary import temporary_password
from journal.entries import differences, record_server
from journal.models import Action
from journal.snapshots import created_account_snapshot

ADMIN_NAME = "Администратор"
DEFAULT_LOGIN = "admin"


class Command(BaseCommand):
    help = "Создаёт локального администратора с временным паролем"

    def add_arguments(self, parser):
        parser.add_argument("--login", default=DEFAULT_LOGIN)

    @transaction.atomic
    def handle(self, *args, **options):
        existing = Account.objects.filter(source=Source.LOCAL, role=Role.ADMIN).first()
        if existing is not None:
            raise CommandError(f"Администратор уже есть: {existing.login}. Новый пароль: sudo ./scripts/change-password.sh {existing.login}")
        login = normalize_login(options["login"])
        if Account.objects.filter(login=login).exists():
            raise CommandError(f"Логин {login} уже занят. Укажите другой: --login <логин>")
        password = temporary_password()
        account = Account.objects.create(
            login=login,
            full_name=ADMIN_NAME,
            source=Source.LOCAL,
            role=Role.ADMIN,
            password_hash=hash_password(password),
            must_change_password=True,
            track_lunch=tracks_lunch_by_default(Role.ADMIN),
        )
        record_server(Action.ACCOUNT_CREATED, account, differences({}, created_account_snapshot(account)))
        self.stdout.write(f"Логин: {login}\nВременный пароль: {password}\nПри первом входе система попросит задать новый пароль.")
