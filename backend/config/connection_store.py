import base64
import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass

from cryptography.fernet import Fernet, InvalidToken

from config.state_files import remove_file

KEY_CONTEXT = b"obedy:database-connection:"
FILE_MODE = 0o600


@dataclass(frozen=True)
class Connection:
    host: str
    port: str
    name: str
    user: str
    password: str
    trust_certificate: bool


def _fernet(secret):
    digest = hashlib.sha256(KEY_CONTEXT + secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def save_connection(path, secret, connection):
    token = _fernet(secret).encrypt(json.dumps(asdict(connection)).encode())
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=directory)
    with os.fdopen(handle, "wb") as file:
        file.write(token)
    os.chmod(temporary, FILE_MODE)
    os.replace(temporary, path)


def load_connection(path, secret):
    try:
        with open(path, "rb") as file:
            token = file.read()
    except FileNotFoundError:
        return None
    try:
        return Connection(**json.loads(_fernet(secret).decrypt(token)))
    except (InvalidToken, ValueError, TypeError):
        return None


def forget_connection(path):
    remove_file(path)
