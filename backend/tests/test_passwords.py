from accounts.passwords import hash_password, verify_password


def test_hash_is_bcrypt_sha256_and_not_plaintext():
    password_hash = hash_password("correct-horse-battery")

    assert password_hash.startswith("bcrypt_sha256$")
    assert "correct-horse-battery" not in password_hash


def test_verify_accepts_right_and_rejects_wrong_password():
    password_hash = hash_password("correct-horse-battery")

    assert verify_password("correct-horse-battery", password_hash)
    assert not verify_password("correct-horse-batterY", password_hash)


def test_same_password_gets_different_salted_hashes():
    assert hash_password("correct-horse-battery") != hash_password("correct-horse-battery")


def test_long_cyrillic_passwords_are_not_truncated():
    base = "пароль" * 13
    password_hash = hash_password(base + "а")

    assert len((base + "а").encode()) > 72
    assert verify_password(base + "а", password_hash)
    assert not verify_password(base + "б", password_hash)
