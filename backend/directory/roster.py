from ldap3 import SUBTREE
from ldap3.utils.conv import escape_filter_chars

from directory.users import MAX_GROUP_DEPTH, PERSON_FILTER, USER_ATTRIBUTES, normalize_dn, read_user

PAGE_SIZE = 500
DOMAIN_COMPONENT = "dc="


def paged_entries(connection, base_dn, search_filter, attributes):
    found = connection.extend.standard.paged_search(
        base_dn, search_filter, SUBTREE, attributes=attributes, paged_size=PAGE_SIZE, generator=False
    )
    return [entry for entry in found or [] if entry.get("dn") and "attributes" in entry]


def domain_root(dn):
    return ",".join(part.strip() for part in dn.split(",") if part.strip().lower().startswith(DOMAIN_COMPONENT))


def child_groups(connection, root, group_dn):
    search_filter = f"(&(objectClass=group)(memberOf={escape_filter_chars(group_dn)}))"
    return [entry["dn"] for entry in paged_entries(connection, root, search_filter, ["cn"])]


def nested_groups(connection, group_dn):
    root = domain_root(group_dn)
    found = {normalize_dn(group_dn)}
    level = [group_dn]
    for _ in range(MAX_GROUP_DEPTH):
        fresh = [child for group in level for child in child_groups(connection, root, group) if normalize_dn(child) not in found]
        if not fresh:
            break
        found.update(normalize_dn(child) for child in fresh)
        level = fresh
    return found


def belongs(user, groups):
    return any(normalize_dn(group) in groups for group in user.groups)


def permitted_users(connection, config):
    people = [read_user(entry) for entry in paged_entries(connection, config.base_dn, PERSON_FILTER, USER_ATTRIBUTES)]
    active = [user for user in people if user.login and not user.disabled]
    if not config.group_dn:
        return active
    groups = nested_groups(connection, config.group_dn)
    return [user for user in active if belongs(user, groups)]
