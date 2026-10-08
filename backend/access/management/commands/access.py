from django.core.management.base import BaseCommand, CommandError

from access.models import AllowedNetwork
from access.networks import PRIVATE_RANGES, InvalidNetwork, parse_network
from access.policy import load_policy
from access.service import DuplicateNetwork, add_network, remove_network, set_private_networks

SWITCH_VALUES = {"on": True, "off": False}


class Command(BaseCommand):
    help = "Доступ к сайту по IP: show | add <адрес> [пометка] | remove <адрес> | lan on|off"

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["show", "add", "remove", "lan"])
        parser.add_argument("value", nargs="?")
        parser.add_argument("note", nargs="?", default="")

    def handle(self, *args, **options):
        handlers = {"show": self.show, "add": self.add, "remove": self.remove, "lan": self.lan}
        handlers[options["action"]](options["value"], options["note"])
        if options["action"] != "show":
            self.show(None, None)

    def show(self, value, note):
        policy = load_policy()
        lan = f"открыта ({', '.join(PRIVATE_RANGES)})" if policy.allow_private else "закрыта"
        self.stdout.write(f"Вся локальная сеть: {lan}")
        self.stdout.write("Сам сервер (127.0.0.1): открыт всегда")
        rows = list(AllowedNetwork.objects.order_by("created_at", "pk"))
        self.stdout.write("Разрешённые адреса:" if rows else "Разрешённых адресов нет")
        for row in rows:
            self.stdout.write(f"  {row.network}  {row.note}".rstrip())

    def add(self, value, note):
        try:
            add_network(self.required(value), note)
        except InvalidNetwork as error:
            raise CommandError("Неверный адрес. Пример: 192.168.1.10 или 192.168.1.0/24") from error
        except DuplicateNetwork as error:
            raise CommandError("Этот адрес уже есть в списке") from error

    def remove(self, value, note):
        try:
            network = str(parse_network(self.required(value)))
        except InvalidNetwork as error:
            raise CommandError("Неверный адрес. Пример: 192.168.1.10 или 192.168.1.0/24") from error
        row = AllowedNetwork.objects.filter(network=network).first()
        if row is None:
            raise CommandError("Такого адреса нет в списке")
        remove_network(row.pk, None)

    def lan(self, value, note):
        if value not in SWITCH_VALUES:
            raise CommandError("Укажите on или off")
        set_private_networks(SWITCH_VALUES[value], None)

    @staticmethod
    def required(value):
        if not value:
            raise CommandError("Укажите адрес, например 192.168.1.10 или 192.168.1.0/24")
        return value
