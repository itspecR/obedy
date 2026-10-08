import json
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.test import Client
from django.utils import timezone

from accounts.cookies import DEVICE_COOKIE, SESSION_COOKIE
from accounts.models import Account, KnownDevice, Role, Source
from accounts.throttle import ServerBusy
from tests.factories import DEFAULT_PASSWORD, make_account

pytestmark = pytest.mark.django_db

WRONG_PASSWORD = "wrong-password-000"
LOGIN_FAILED = {"detail": "Неверный логин или пароль. После 5 ошибок подряд вход закрывается на 15 минут"}


def post_login(client, login="ivanov.ii", password=DEFAULT_PASSWORD, **headers):
    body = json.dumps({"login": login, "password": password})
    return client.post("/api/auth/login", body, content_type="application/json", **headers)


def fail_times(client, count, login="ivanov.ii"):
    return [post_login(client, login=login, password=WRONG_PASSWORD).status_code for _ in range(count)]


@pytest.fixture
def account():
    return make_account()


def test_successful_login_sets_httponly_session_cookie(account):
    response = post_login(Client())

    assert response.status_code == 200
    assert response.json() == {
        "login": "ivanov.ii",
        "display_name": "ivanov.ii",
        "role": Role.EMPLOYEE,
        "source": Source.LOCAL,
        "must_change_password": True,
        "weak_password": False,
    }
    cookie = response.cookies[SESSION_COOKIE]
    assert cookie["httponly"] is True
    assert cookie["samesite"] == "Lax"


def test_login_is_case_and_space_insensitive(account):
    assert post_login(Client(), login="  Ivanov.II ").status_code == 200


def test_display_name_and_role_come_from_the_account():
    make_account(full_name="Петрова Анна Андреевна", role=Role.HR)

    body = post_login(Client()).json()

    assert body["display_name"] == "Петрова Анна Андреевна"
    assert body["role"] == Role.HR


def test_me_returns_current_account_after_login(account):
    client = Client()
    post_login(client)

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["login"] == "ivanov.ii"


def test_me_reflects_role_change_without_new_login(account):
    client = Client()
    post_login(client)
    Account.objects.update(role=Role.ADMIN)

    assert client.get("/api/auth/me").json()["role"] == Role.ADMIN


def test_me_without_session_is_rejected():
    response = Client().get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Войдите в систему"}


def test_logout_ends_session(account):
    client = Client()
    post_login(client)

    assert client.post("/api/auth/logout", content_type="application/json").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_wrong_password_and_unknown_login_give_same_answer(account):
    wrong = post_login(Client(), password=WRONG_PASSWORD)
    unknown = post_login(Client(), login="nobody.xx")

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == LOGIN_FAILED


def test_inactive_account_cannot_log_in(account):
    Account.objects.update(is_active=False)

    assert post_login(Client()).status_code == 401


def test_deactivation_ends_open_sessions(account):
    client = Client()
    post_login(client)
    Account.objects.update(is_active=False)

    assert client.get("/api/auth/me").status_code == 401


def test_account_without_local_password_cannot_log_in(account):
    Account.objects.update(password_hash="")

    assert post_login(Client()).status_code == 401


def test_domain_account_is_not_checked_against_local_hash(account):
    Account.objects.update(source=Source.DOMAIN)

    assert post_login(Client()).status_code == 401


def test_five_wrong_passwords_lock_account_for_fifteen_minutes(account):
    client = Client()

    assert fail_times(client, 6) == [401] * 6
    locked = post_login(client)
    assert locked.status_code == 401
    assert locked.json() == LOGIN_FAILED
    assert Account.objects.get().locked_until > timezone.now() + timedelta(minutes=14)


def test_right_and_wrong_password_look_the_same_during_lock(account):
    fail_times(Client(), 5)
    locked_until = Account.objects.get().locked_until

    right = post_login(Client())
    wrong = post_login(Client(), password=WRONG_PASSWORD)

    assert right.status_code == wrong.status_code == 401
    assert right.json() == wrong.json() == LOGIN_FAILED
    assert SESSION_COOKIE not in right.cookies
    assert Account.objects.get().locked_until == locked_until


def test_account_opens_after_lock_expires(account):
    fail_times(Client(), 5)
    Account.objects.update(locked_until=timezone.now() - timedelta(seconds=1))

    assert post_login(Client()).status_code == 200


def test_successful_login_resets_failed_counter(account):
    client = Client()
    fail_times(client, 4)
    post_login(client)

    assert Account.objects.get().failed_count == 0


def test_successful_login_marks_device(account):
    response = post_login(Client())

    assert response.cookies[DEVICE_COOKIE]["httponly"] is True
    assert KnownDevice.objects.count() == 1


def test_known_device_ignores_account_lock_caused_by_others(account):
    trusted = Client()
    post_login(trusted)
    trusted.post("/api/auth/logout", content_type="application/json")
    fail_times(Client(), 5)

    assert post_login(Client()).status_code == 401
    assert post_login(trusted).status_code == 200


def test_five_failures_from_known_device_forget_it(account):
    trusted = Client()
    post_login(trusted)
    fail_times(trusted, 5)

    assert KnownDevice.objects.count() == 0
    assert fail_times(trusted, 5) == [401] * 5
    assert Account.objects.get().locked_until is not None


def test_session_lives_eight_hours(account):
    post_login(Client())

    session = Account.objects.get().sessions.get()
    assert timezone.now() + timedelta(hours=7, minutes=59) < session.expires_at < timezone.now() + timedelta(hours=8, minutes=1)


def test_busy_server_answers_503(account):
    with patch("accounts.verification.password_check_slot", side_effect=ServerBusy):
        response = post_login(Client())

    assert response.status_code == 503
    assert response.json() == {"detail": "Сервер занят. Попробуйте ещё раз через минуту"}


def test_foreign_origin_is_rejected(account):
    assert post_login(Client(), HTTP_ORIGIN="http://evil.example").status_code == 403


def test_same_origin_is_accepted(account):
    assert post_login(Client(), HTTP_ORIGIN="http://testserver").status_code == 200


def test_https_origin_is_accepted_behind_tls_proxy(account):
    response = post_login(Client(), HTTP_ORIGIN="https://testserver", HTTP_X_FORWARDED_PROTO="https", HTTP_HOST="testserver")

    assert response.status_code == 200


def test_plain_http_origin_is_rejected_on_https_site(account):
    by_origin = post_login(Client(), HTTP_ORIGIN="http://testserver", HTTP_X_FORWARDED_PROTO="https", HTTP_HOST="testserver")
    by_referer = post_login(Client(), HTTP_REFERER="http://testserver/login", HTTP_X_FORWARDED_PROTO="https", HTTP_HOST="testserver")

    assert by_origin.status_code == by_referer.status_code == 403
