import secrets

TEMPORARY_PASSWORD_LENGTH = 10
ALPHABET = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def temporary_password(length=TEMPORARY_PASSWORD_LENGTH):
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
