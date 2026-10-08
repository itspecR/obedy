from django.core.management.base import BaseCommand, CommandError

from accounts.credentials import set_temporary_password
from accounts.models import Account, Source
from accounts.names import normalize_login
from accounts.temporary import temporary_password


class Command(BaseCommand):
    help = "Выдаёт новый временный пароль локальной учётной записи (для восстановления доступа с сервера)"

    def add_arguments(self, parser):
        parser.add_argument("login")

    def handle(self, *args, **options):
        account = Account.objects.filter(login=normalize_login(options["login"])).first()
        if account is None:
            raise CommandError("Учётная запись с таким логином не найдена")
        if account.source != Source.LOCAL:
            raise CommandError("Это доменная учётная запись: её пароль меняется в Active Directory")
        password = temporary_password()
        set_temporary_password(account, password)
        self.stdout.write(f"Логин: {account.login}\nВременный пароль: {password}\nПри входе система попросит задать новый пароль.")
