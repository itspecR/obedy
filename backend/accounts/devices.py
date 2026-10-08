from datetime import timedelta

from accounts.models import KnownDevice
from accounts.tokens import hash_token, new_token

DEVICE_LIFETIME = timedelta(days=365)


def remember_device(account, now):
    token = new_token()
    KnownDevice.objects.create(
        token_hash=hash_token(token),
        account=account,
        expires_at=now + DEVICE_LIFETIME,
    )
    return token


def find_known_device(account, token, now):
    return KnownDevice.objects.filter(
        account=account,
        token_hash=hash_token(token),
        expires_at__gt=now,
    ).first()


def forget_all_devices(account):
    KnownDevice.objects.filter(account=account).delete()


def delete_expired_devices(now):
    deleted, _ = KnownDevice.objects.filter(expires_at__lte=now).delete()
    return deleted
