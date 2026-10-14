from accounts.temporary import ALPHABET, temporary_password


def test_temporary_password_is_ten_unambiguous_characters():
    password = temporary_password()

    assert len(password) == 10
    assert set(password) <= set(ALPHABET)
    assert not set("0O1lI") & set(ALPHABET)


def test_temporary_passwords_differ():
    assert len({temporary_password() for _ in range(200)}) == 200
