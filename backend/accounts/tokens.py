import hashlib
import secrets

TOKEN_BYTES = 32


def new_token():
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()
