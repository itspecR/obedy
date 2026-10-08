def display_name(account):
    return account.full_name or account.login


def normalize_login(login):
    return login.strip().lower()
