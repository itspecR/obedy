from django.core.management.base import BaseCommand, CommandError

from accounts.first_admin import DEFAULT_LOGIN, AdminExists, LoginTaken, create_first_admin


class Command(BaseCommand):
    help = "Создаёт локального администратора с временным паролем"

    def add_arguments(self, parser):
        parser.add_argument("--login", default=DEFAULT_LOGIN)

    def handle(self, *args, **options):
        try:
            account, password = create_first_admin(options["login"])
        except AdminExists as error:
            raise CommandError(f"Администратор уже есть: {error.login}. Новый пароль: sudo ./scripts/change-password.sh {error.login}") from error
        except LoginTaken as error:
            raise CommandError(f"Логин {error} уже занят. Укажите другой: --login <логин>") from error
        self.stdout.write(f"Логин: {account.login}\nВременный пароль: {password}\nПри первом входе система попросит задать новый пароль.")
