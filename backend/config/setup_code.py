import hashlib
import hmac
import os
import secrets

from config.state_files import remove_file

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_GROUPS = 3
GROUP_LENGTH = 4
FILE_MODE = 0o600


def _digest(code):
    return hashlib.sha256(code.replace("-", "").replace(" ", "").upper().encode()).hexdigest()


def issue_code(path):
    raw = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_GROUPS * GROUP_LENGTH))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as file:
        file.write(_digest(raw))
    os.chmod(path, FILE_MODE)
    return "-".join(raw[index : index + GROUP_LENGTH] for index in range(0, len(raw), GROUP_LENGTH))


def code_matches(path, code):
    try:
        with open(path) as file:
            expected = file.read().strip()
    except FileNotFoundError:
        return False
    return bool(code) and hmac.compare_digest(expected, _digest(code))


def forget_code(path):
    remove_file(path)
