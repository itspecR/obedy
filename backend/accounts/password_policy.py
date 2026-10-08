from django.contrib.auth.password_validation import CommonPasswordValidator
from django.core.exceptions import ValidationError

MIN_LENGTH = 10
MAX_LENGTH = 128
MIN_DISTINCT = 4
MIN_WORD = 4
SEQUENCES = (
    "0123456789",
    "abcdefghijklmnopqrstuvwxyz",
    "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
    "йцукенгшщзхъ",
    "фывапролджэ",
    "ячсмитьбю",
)

TOO_SHORT = f"Пароль должен быть не короче {MIN_LENGTH} символов"
TOO_LONG = f"Пароль должен быть не длиннее {MAX_LENGTH} символов"
ONLY_DIGITS = "Пароль не может состоять только из цифр"
TOO_UNIFORM = "В пароле слишком мало разных символов"
SEQUENCE = "Пароль не должен быть последовательностью вроде 1234567890 или qwertyuiop"
COMMON = "Этот пароль слишком распространён, придумайте другой"
PERSONAL = "Пароль не должен содержать логин, имя или фамилию"

_common = CommonPasswordValidator()


class WeakPassword(ValueError):
    pass


def length_problem(raw):
    if len(raw) < MIN_LENGTH:
        return TOO_SHORT
    return TOO_LONG if len(raw) > MAX_LENGTH else None


def is_sequence(lowered):
    for sequence in SEQUENCES:
        for line in (sequence, sequence[::-1]):
            if lowered in line * (len(lowered) // len(line) + 2):
                return True
    return False


def is_common(raw):
    try:
        _common.validate(raw)
    except ValidationError:
        return True
    return False


def contains_personal(lowered, words):
    return any(len(word) >= MIN_WORD and word in lowered for word in words)


def password_problem(raw, words=()):
    length = length_problem(raw)
    if length:
        return length
    lowered = raw.lower()
    checks = (
        (raw.isdigit, ONLY_DIGITS),
        (lambda: len(set(lowered)) < MIN_DISTINCT, TOO_UNIFORM),
        (lambda: is_sequence(lowered), SEQUENCE),
        (lambda: is_common(raw), COMMON),
        (lambda: contains_personal(lowered, words), PERSONAL),
    )
    return next((message for failed, message in checks if failed()), None)


def check_password_rules(raw, words=()):
    problem = password_problem(raw, words)
    if problem:
        raise WeakPassword(problem)


def name_words(text):
    return [part for part in (text or "").lower().replace(".", " ").replace("-", " ").split() if part]


def personal_words(account):
    return [account.login.lower(), *name_words(account.full_name)]
