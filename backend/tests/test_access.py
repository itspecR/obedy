import io
import json

import pytest
from django.core.management import CommandError, call_command
from django.test import Client

from access.models import AllowedNetwork
from access.networks import InvalidNetwork, is_allowed, parse_network
from access.policy import forget_policy
from accounts.models import Role
from tests.factories import DEFAULT_PASSWORD, make_account

pytestmark = pytest.mark.django_db

ADMIN_ADDRESS = "192.168.5.20"
RDP_ADDRESS = "10.1.1.7"


@pytest.fixture(autouse=True)
def fresh_policy():
    forget_policy()
    yield
    forget_policy()


def client_from(address):
    return Client(HTTP_X_REAL_IP=address)


def admin_client(address=ADMIN_ADDRESS, role=Role.ADMIN):
    make_account(login="boss", role=role, must_change_password=False)
    client = client_from(address)
    client.post("/api/auth/login", json.dumps({"login": "boss", "password": DEFAULT_PASSWORD}), content_type="application/json")
    return client


def check(address):
    return client_from(address).get("/api/access/check").status_code


def put_private(client, enabled):
    return client.put("/api/access/private", json.dumps({"enabled": enabled}), content_type="application/json")


def add(client, network, note=""):
    return client.post("/api/access/networks", json.dumps({"network": network, "note": note}), content_type="application/json")


def test_networks_are_parsed_and_normalized():
    assert str(parse_network(" 192.168.1.10 ")) == "192.168.1.10/32"
    assert str(parse_network("192.168.1.77/24")) == "192.168.1.0/24"
    with pytest.raises(InvalidNetwork):
        parse_network("300.1.1.1")
    with pytest.raises(InvalidNetwork):
        parse_network("")


@pytest.mark.parametrize(
    ("address", "allow_private", "expected"),
    [
        ("127.0.0.1", False, True),
        ("10.20.30.40", True, True),
        ("172.31.0.5", True, True),
        ("172.32.0.5", True, False),
        ("192.168.0.9", False, False),
        ("8.8.8.8", True, False),
        ("not-an-ip", True, False),
        ("", True, False),
    ],
)
def test_private_networks_and_loopback(address, allow_private, expected):
    assert is_allowed(address, allow_private, ()) is expected


def test_listed_network_allows_its_addresses_only():
    networks = (parse_network("10.1.1.0/30"),)

    assert is_allowed("10.1.1.2", False, networks)
    assert not is_allowed("10.1.1.9", False, networks)


def test_whole_local_network_is_open_after_install():
    assert check(RDP_ADDRESS) == 204
    assert check("8.8.8.8") == 403


def test_check_uses_real_ip_set_by_nginx():
    client = admin_client()
    add(client, RDP_ADDRESS)
    add(client, ADMIN_ADDRESS)
    put_private(client, False)

    assert check(RDP_ADDRESS) == 204
    assert check("10.1.1.8") == 403
    assert Client(REMOTE_ADDR="127.0.0.1").get("/api/access/check").status_code == 204


def test_admin_sees_policy_and_own_address():
    body = admin_client().get("/api/access").json()

    assert body["allow_private"] is True
    assert body["your_address"] == ADMIN_ADDRESS
    assert body["private_ranges"] == ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
    assert body["networks"] == []


def test_admin_adds_and_removes_networks():
    client = admin_client()

    created = add(client, "10.1.1.7", "RDP-1")
    network_id = created.json()["networks"][0]["id"]
    removed = client.delete(f"/api/access/networks/{network_id}")

    assert created.status_code == 201
    assert created.json()["networks"][0] == {"id": network_id, "network": "10.1.1.7/32", "note": "RDP-1"}
    assert removed.status_code == 200 and removed.json()["networks"] == []


def test_invalid_and_duplicate_networks_are_explained():
    client = admin_client()
    add(client, "10.1.1.7")

    invalid = add(client, "10.1.1.999")
    duplicate = add(client, "10.1.1.7/32")

    assert invalid.status_code == 400 and invalid.json()["detail"] == "Неверный адрес. Пример: 192.168.1.10 или 192.168.1.0/24"
    assert duplicate.status_code == 409 and duplicate.json()["detail"] == "Этот адрес уже есть в списке"


def test_turning_off_local_network_is_refused_when_admin_would_lose_access():
    client = admin_client()

    response = put_private(client, False)

    assert response.status_code == 400
    assert response.json()["detail"] == f"Нельзя: ваш адрес {ADMIN_ADDRESS} потеряет доступ. Сначала добавьте его в список"
    assert check(RDP_ADDRESS) == 204


def test_turning_off_local_network_works_when_admin_is_listed():
    client = admin_client()
    add(client, ADMIN_ADDRESS)

    response = put_private(client, False)

    assert response.status_code == 200 and response.json()["allow_private"] is False
    assert check(RDP_ADDRESS) == 403
    assert check(ADMIN_ADDRESS) == 204


def test_removing_own_address_is_refused_when_it_is_the_only_way_in():
    client = admin_client()
    created = add(client, ADMIN_ADDRESS)
    put_private(client, False)

    response = client.delete(f"/api/access/networks/{created.json()['networks'][0]['id']}")

    assert response.status_code == 400
    assert AllowedNetwork.objects.count() == 1


def test_unknown_network_gives_not_found():
    assert admin_client().delete("/api/access/networks/999").status_code == 404


@pytest.mark.parametrize("role", [Role.EMPLOYEE, Role.HR])
def test_only_admin_manages_access(role):
    client = admin_client(role=role)

    assert client.get("/api/access").status_code == 403
    assert add(client, RDP_ADDRESS).status_code == 403
    assert put_private(client, False).status_code == 403


def test_guest_cannot_manage_access():
    assert client_from(ADMIN_ADDRESS).get("/api/access").status_code == 401


def run(*args):
    out = io.StringIO()
    call_command("access", *args, stdout=out)
    return out.getvalue()


def test_server_command_manages_access_without_lockout_guard():
    run("add", "10.1.1.7", "RDP-1")
    text = run("lan", "off")

    assert "Вся локальная сеть: закрыта" in text
    assert "10.1.1.7/32  RDP-1" in text
    assert check(RDP_ADDRESS) == 204
    assert check("10.1.1.8") == 403

    run("remove", "10.1.1.7")
    assert "Разрешённых адресов нет" in run("lan", "on")


def test_server_command_explains_mistakes():
    with pytest.raises(CommandError, match="Неверный адрес"):
        run("add", "nonsense")
    with pytest.raises(CommandError, match="нет в списке"):
        run("remove", "10.9.9.9")
    with pytest.raises(CommandError, match="on или off"):
        run("lan", "maybe")
