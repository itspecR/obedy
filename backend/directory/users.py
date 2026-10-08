import uuid
from dataclasses import dataclass

from ldap3 import BASE, SUBTREE
from ldap3.utils.conv import escape_filter_chars

ACCOUNT_DISABLED_FLAG = 0x2
MAX_GROUP_DEPTH = 10
USER_ATTRIBUTES = ["sAMAccountName", "displayName", "cn", "department", "title", "userAccountControl", "memberOf", "objectGUID"]


@dataclass(frozen=True)
class DirectoryUser:
    dn: str
    login: str
    full_name: str
    department: str
    position: str
    external_id: str
    disabled: bool
    groups: tuple


def user_filter(login):
    return f"(&(objectClass=user)(sAMAccountName={escape_filter_chars(login)}))"


def values(attributes, name):
    value = attributes.get(name)
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


def text(attributes, name):
    found = values(attributes, name)
    return str(found[0]).strip() if found else ""


def guid(raw_attributes):
    found = values(raw_attributes, "objectGUID")
    return str(uuid.UUID(bytes_le=found[0])) if found else ""


def is_disabled(attributes):
    flags = text(attributes, "userAccountControl")
    return flags.isdigit() and bool(int(flags) & ACCOUNT_DISABLED_FLAG)


def read_user(entry):
    attributes = entry.get("attributes", {})
    return DirectoryUser(
        dn=entry["dn"],
        login=text(attributes, "sAMAccountName").lower(),
        full_name=text(attributes, "displayName") or text(attributes, "cn"),
        department=text(attributes, "department"),
        position=text(attributes, "title"),
        external_id=guid(entry.get("raw_attributes", {})),
        disabled=is_disabled(attributes),
        groups=tuple(str(group) for group in values(attributes, "memberOf")),
    )


def entries(connection):
    return [entry for entry in connection.response or [] if entry.get("dn") and "attributes" in entry]


def find_user(connection, base_dn, login):
    connection.search(base_dn, user_filter(login), SUBTREE, attributes=USER_ATTRIBUTES, size_limit=2)
    found = entries(connection)
    return read_user(found[0]) if len(found) == 1 else None


def normalize_dn(dn):
    return ",".join(part.strip() for part in dn.split(",")).lower()


def parent_groups(connection, group_dn):
    connection.search(group_dn, "(objectClass=*)", BASE, attributes=["memberOf"])
    found = entries(connection)
    return [str(group) for group in values(found[0]["attributes"], "memberOf")] if found else []


def is_member(connection, user, group_dn):
    target = normalize_dn(group_dn)
    seen = set()
    level = list(user.groups)
    for _ in range(MAX_GROUP_DEPTH):
        fresh = [group for group in level if normalize_dn(group) not in seen]
        if any(normalize_dn(group) == target for group in fresh):
            return True
        if not fresh:
            return False
        seen.update(normalize_dn(group) for group in fresh)
        level = [parent for group in fresh for parent in parent_groups(connection, group)]
    return False


def group_exists(connection, group_dn):
    connection.search(group_dn, "(objectClass=group)", BASE, attributes=["cn"])
    return bool(entries(connection))


def count_users(connection, base_dn, limit):
    connection.search(base_dn, "(objectClass=user)", SUBTREE, attributes=["sAMAccountName"], size_limit=limit)
    return len(entries(connection))
