import re
from dataclasses import dataclass

from directory.models import SETTINGS_ID, DirectorySettings, Mode
from directory.vault import unseal

DEFAULT_PORTS = {Mode.LDAPS: 636, Mode.STARTTLS: 389, Mode.PLAIN: 389}
SERVER_SEPARATORS = re.compile(r"[\s,;]+")


@dataclass(frozen=True)
class DirectoryConfig:
    enabled: bool
    servers: tuple
    mode: str
    port: int
    ca_certificate: str
    bind_user: str
    bind_password: str
    base_dn: str
    group_dn: str
    session_days: int

    @property
    def complete(self):
        return bool(self.servers and self.bind_user and self.bind_password and self.base_dn)

    @property
    def ready(self):
        return self.enabled and self.complete


def stored_settings():
    return DirectorySettings.objects.get_or_create(pk=SETTINGS_ID)[0]


def split_servers(text):
    return tuple(item for item in SERVER_SEPARATORS.split(text or "") if item)


def config_from(stored):
    return DirectoryConfig(
        enabled=stored.enabled,
        servers=split_servers(stored.servers),
        mode=stored.mode,
        port=stored.port or DEFAULT_PORTS[stored.mode],
        ca_certificate=stored.ca_certificate,
        bind_user=stored.bind_user,
        bind_password=unseal(stored.bind_password),
        base_dn=stored.base_dn,
        group_dn=stored.group_dn,
        session_days=stored.session_days,
    )


def current_config():
    return config_from(stored_settings())
