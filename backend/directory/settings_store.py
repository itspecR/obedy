from directory.certificates import checked_certificate
from directory.config import split_servers, stored_settings
from directory.vault import seal

REQUIRED_FIELDS = (
    ("servers", "серверы"),
    ("bind_user", "сервисная учётная запись"),
    ("bind_password", "пароль сервисной учётной записи"),
    ("base_dn", "база поиска"),
)


class IncompleteSettings(ValueError):
    def __init__(self, missing):
        super().__init__(missing)
        self.missing = missing


def missing_fields(values, has_password):
    present = {
        "servers": bool(split_servers(values["servers"])),
        "bind_user": bool(values["bind_user"].strip()),
        "bind_password": bool(values["bind_password"]) or has_password,
        "base_dn": bool(values["base_dn"].strip()),
    }
    return [label for name, label in REQUIRED_FIELDS if not present[name]]


def save_settings(values):
    stored = stored_settings()
    certificate = checked_certificate(values["ca_certificate"])
    missing = missing_fields(values, bool(stored.bind_password))
    if values["enabled"] and missing:
        raise IncompleteSettings(missing)
    stored.enabled = values["enabled"]
    stored.servers = " ".join(split_servers(values["servers"]))
    stored.mode = values["mode"]
    stored.port = values["port"]
    stored.ca_certificate = certificate
    stored.bind_user = values["bind_user"].strip()
    stored.base_dn = values["base_dn"].strip()
    stored.group_dn = values["group_dn"].strip()
    stored.session_days = values["session_days"]
    if values["bind_password"]:
        stored.bind_password = seal(values["bind_password"])
    stored.save()
    return stored
