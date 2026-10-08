import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

KEY_CONTEXT = b"obedy:directory-bind-password:"


def _fernet():
    digest = hashlib.sha256(KEY_CONTEXT + settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def seal(text):
    return _fernet().encrypt(text.encode()).decode() if text else ""


def unseal(token):
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        return ""
