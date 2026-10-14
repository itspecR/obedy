import json

import pytest
from django.test import Client

from accounts.models import Account
from accounts.password_policy import (
    COMMON, ONLY_DIGITS, PERSONAL, SEQUENCE, TOO_LONG, TOO_SHORT, TOO_UNIFORM, password_problem, personal_words,
)
from tests.factories import DEFAULT_PASSWORD, make_account

pytestmark = pytest.mark.django_db

GOOD_PASSWORD = "лиса-в-снегу-2026"


def post_json(client, url, payload):
    return client.post(url, json.dumps(payload), content_type="application/json")


@pytest.mark.parametrize(
    ("password", "problem"),
    [
        ("short", TOO_SHORT),
        ("x" * 129, TOO_LONG),
        ("8264019375", ONLY_DIGITS),
        ("aaaaabbbbb", TOO_UNIFORM),
        ("qwertyuiop", SEQUENCE),
        ("ЙЦУКЕНГШЩЗ", SEQUENCE),
        ("password123", COMMON),
    ],
)
def test_weak_passwords_are_rejected(password, problem):
    assert password_problem(password) == problem


@pytest.mark.parametrize("password", [GOOD_PASSWORD, "correct-horse-battery", "xxxAb9#kLm2qR"])
def test_good_passwords_pass(password):
    assert password_problem(password) is None


def test_personal_words_block_login_and_name():
    account = make_account(login="orlov.oleg", full_name="Орлов Олег")
    words = personal_words(account)

    assert password_problem("my-orlov.oleg-pass", words) == PERSONAL
    assert password_problem("орлов-навсегда-7", words) == PERSONAL
    assert password_problem(GOOD_PASSWORD, words) is None


def test_login_with_weak_old_password_requires_a_change():
    make_account(password="qwertyuiop", must_change_password=False)
    client = Client()

    body = post_json(client, "/api/auth/login", {"login": "ivanov.ii", "password": "qwertyuiop"}).json()
    changed = post_json(client, "/api/auth/change-password", {"new_password": GOOD_PASSWORD, "current_password": "qwertyuiop"}).json()

    assert body["must_change_password"] is True and body["weak_password"] is True
    assert changed["weak_password"] is False and changed["must_change_password"] is False


def test_weak_password_change_requires_the_current_password():
    make_account(password="qwertyuiop", must_change_password=False)
    client = Client()
    post_json(client, "/api/auth/login", {"login": "ivanov.ii", "password": "qwertyuiop"})

    response = post_json(client, "/api/auth/change-password", {"new_password": GOOD_PASSWORD})

    assert response.status_code == 400
    assert Account.objects.get().weak_password is True


def test_login_with_good_password_keeps_the_account_as_is():
    make_account(must_change_password=False)

    body = post_json(Client(), "/api/auth/login", {"login": "ivanov.ii", "password": DEFAULT_PASSWORD}).json()

    assert body["must_change_password"] is False and body["weak_password"] is False
