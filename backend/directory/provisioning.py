from accounts.models import Account, Role, Source


def existing_account(user):
    if user.external_id:
        found = Account.objects.filter(external_id=user.external_id).first()
        if found is not None:
            return found
    return Account.objects.filter(login=user.login, source=Source.DOMAIN).first()


def profile_of(user):
    return {
        "login": user.login,
        "full_name": user.full_name,
        "external_id": user.external_id or None,
    }


def is_outdated(account, user):
    profile = profile_of(user)
    return not account.in_directory or any(getattr(account, field) != value for field, value in profile.items())


def save_account(user, account=None):
    account = account or existing_account(user) or Account(source=Source.DOMAIN, role=Role.EMPLOYEE)
    for field, value in profile_of(user).items():
        setattr(account, field, value)
    account.source = Source.DOMAIN
    account.password_hash = ""
    account.in_directory = True
    account.save()
    return account
