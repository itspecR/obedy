import json

import pytest
from django.test import Client, RequestFactory
from ninja.errors import HttpError

from accounts.cookies import SESSION_COOKIE
from accounts.models import Account, Source
from accounts.security import PASSWORD_CHANGE_REQUIRED, SessionAuth
from tests.factories import DEFAULT_PASSWORD, make_account

pytestmark = pytest.mark.django_db

NEW_PASSWORD = "brand-new-password-42"


def post_json(client, url, payload):
    return client.post(url, json.dumps(payload), content_type="application/json")


def logged_in_client(password=DEFAULT_PASSWORD):
    client = Client()
    post_json(client, "/api/auth/login", {"login": "ivanov.ii", "password": password})
    return client


def change(client, new=NEW_PASSWORD):
    return post_json(client, "/api/auth/change-password", {"new_password": new})


def voluntary_change(client, current):
    return post_json(client, "/api/auth/change-password", {"current_password": current, "new_password": NEW_PASSWORD})


@pytest.fixture
def account():
    return make_account()


@pytest.fixture
def settled_account():
    return make_account(must_change_password=False)


def test_change_password_clears_must_change_flag(account):
    response = change(logged_in_client())

    assert response.status_code == 200
    assert response.json()["must_change_password"] is False
    assert Account.objects.get().must_change_password is False


def test_new_password_works_and_old_does_not(account):
    change(logged_in_client())

    old = post_json(Client(), "/api/auth/login", {"login": "ivanov.ii", "password": DEFAULT_PASSWORD})
    new = post_json(Client(), "/api/auth/login", {"login": "ivanov.ii", "password": NEW_PASSWORD})
    assert old.status_code == 401
    assert new.status_code == 200


def test_change_keeps_current_session_and_ends_others(account):
    current = logged_in_client()
    other = logged_in_client()

    change(current)

    assert current.get("/api/auth/me").status_code == 200
    assert other.get("/api/auth/me").status_code == 401


def test_voluntary_change_requires_current_password(settled_account):
    response = change(logged_in_client())

    assert response.status_code == 400
    assert response.json() == {"detail": "Текущий пароль указан неверно"}


def test_voluntary_change_with_current_password_works(settled_account):
    assert voluntary_change(logged_in_client(), DEFAULT_PASSWORD).status_code == 200


def test_repeated_wrong_current_password_locks_account(settled_account):
    client = logged_in_client()
    statuses = [voluntary_change(client, "not-my-password").status_code for _ in range(6)]

    assert statuses == [400, 400, 400, 400, 423, 423]
    assert voluntary_change(client, DEFAULT_PASSWORD).status_code == 423


def test_short_new_password_is_rejected(account):
    response = change(logged_in_client(), new="short")

    assert response.status_code == 400
    assert response.json() == {"detail": "Пароль должен быть не короче 10 символов"}


def test_new_password_must_differ_from_current(account):
    response = change(logged_in_client(), new=DEFAULT_PASSWORD)

    assert response.status_code == 400
    assert response.json() == {"detail": "Новый пароль должен отличаться от текущего"}


def test_domain_account_cannot_change_password_here(settled_account):
    client = logged_in_client()
    Account.objects.update(source=Source.DOMAIN)

    response = voluntary_change(client, DEFAULT_PASSWORD)

    assert response.status_code == 400
    assert response.json() == {"detail": "Пароль доменной учётной записи меняется в Windows, а не здесь"}


def test_change_password_requires_login():
    assert change(Client()).status_code == 401


def auth_request(client):
    request = RequestFactory().get("/")
    request.COOKIES[SESSION_COOKIE] = client.cookies[SESSION_COOKIE].value
    return request


def test_strict_auth_blocks_until_password_changed(account):
    client = logged_in_client()
    strict = SessionAuth()

    with pytest.raises(HttpError) as error:
        strict(auth_request(client))
    assert error.value.status_code == 403
    assert str(error.value) == PASSWORD_CHANGE_REQUIRED

    change(client)
    assert strict(auth_request(client)) is not None
