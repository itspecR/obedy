from datetime import timedelta

from accounts.models import Session
from accounts.tokens import hash_token, new_token

SESSION_LIFETIME = timedelta(hours=8)


def create_session(account, now):
    token = new_token()
    Session.objects.create(
        token_hash=hash_token(token),
        account=account,
        account_version=account.version,
        expires_at=now + SESSION_LIFETIME,
    )
    return token


def find_active_session(token, now):
    session = (
        Session.objects.select_related("account")
        .filter(token_hash=hash_token(token), expires_at__gt=now)
        .first()
    )
    if session is None or not is_session_valid(session):
        return None
    return session


def is_session_valid(session):
    account = session.account
    return account.is_active and account.version == session.account_version


def revoke_session(token):
    Session.objects.filter(token_hash=hash_token(token)).delete()


def revoke_other_sessions(account, keep_token):
    Session.objects.filter(account=account).exclude(token_hash=hash_token(keep_token)).delete()


def revoke_all_sessions(account):
    Session.objects.filter(account=account).delete()


def delete_expired_sessions(now):
    deleted, _ = Session.objects.filter(expires_at__lte=now).delete()
    return deleted
