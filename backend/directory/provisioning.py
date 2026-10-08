from accounts.models import Account, Role, Source


def existing_account(user):
    if user.external_id:
        found = Account.objects.filter(external_id=user.external_id).first()
        if found is not None:
            return found
    return Account.objects.filter(login=user.login, source=Source.DOMAIN).first()


def save_account(user):
    account = existing_account(user) or Account(source=Source.DOMAIN, role=Role.EMPLOYEE)
    account.login = user.login
    account.full_name = user.full_name
    account.department = user.department
    account.position = user.position
    account.external_id = user.external_id or None
    account.source = Source.DOMAIN
    account.password_hash = ""
    account.save()
    return account
