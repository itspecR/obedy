DOMAIN_SEPARATOR = "\\"
REALM_SEPARATOR = "@"


def display_name(account):
    return account.full_name or account.login


def normalize_login(login):
    name = login.strip().lower().rsplit(DOMAIN_SEPARATOR, 1)[-1]
    return name.split(REALM_SEPARATOR, 1)[0].strip()
