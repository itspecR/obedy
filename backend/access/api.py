from ninja import Field, Router, Schema, Status
from ninja.errors import HttpError

from access.client import client_address
from access.models import AllowedNetwork
from access.networks import PRIVATE_RANGES, InvalidNetwork
from access.policy import current_policy, load_policy
from access.service import DuplicateNetwork, LockoutRisk, NetworkNotFound, add_network, remove_network, set_private_networks
from accounts.permissions import require_admin
from accounts.security import session_auth
from journal.entries import differences, record, record_changes, removed
from journal.models import Action
from journal.snapshots import network_snapshot, private_snapshot

NOTE_MAX_LENGTH = 120

INVALID_NETWORK = "Неверный адрес. Пример: 192.168.1.10 или 192.168.1.0/24"
DUPLICATE_NETWORK = "Этот адрес уже есть в списке"
NETWORK_NOT_FOUND = "Адрес не найден. Обновите страницу"

router = Router(tags=["Доступ"])


class NetworkOut(Schema):
    id: int
    network: str
    note: str


class AccessOut(Schema):
    allow_private: bool
    private_ranges: list[str]
    your_address: str
    networks: list[NetworkOut]


class NetworkIn(Schema):
    network: str
    note: str = Field("", max_length=NOTE_MAX_LENGTH)


class PrivateIn(Schema):
    enabled: bool


def lockout_message(address):
    return f"Нельзя: ваш адрес {address} потеряет доступ. Сначала добавьте его в список"


def overview(request):
    return AccessOut(
        allow_private=load_policy().allow_private,
        private_ranges=list(PRIVATE_RANGES),
        your_address=client_address(request),
        networks=[NetworkOut(id=item.pk, network=item.network, note=item.note) for item in AllowedNetwork.objects.order_by("created_at", "pk")],
    )


@router.get("/check", auth=None, response={204: None, 403: None})
def check(request):
    allowed = current_policy().allows(client_address(request))
    return Status(204 if allowed else 403, None)


@router.get("", auth=session_auth, response=AccessOut)
def show(request):
    require_admin(request)
    return overview(request)


@router.post("/networks", auth=session_auth, response={201: AccessOut})
def create(request, payload: NetworkIn):
    require_admin(request)
    try:
        created = add_network(payload.network, payload.note)
    except InvalidNetwork as error:
        raise HttpError(400, INVALID_NETWORK) from error
    except DuplicateNetwork as error:
        raise HttpError(409, DUPLICATE_NETWORK) from error
    record(request, Action.NETWORK_ADDED, rows=differences({}, network_snapshot(created)))
    return Status(201, overview(request))


@router.delete("/networks/{network_id}", auth=session_auth, response=AccessOut)
def delete(request, network_id: int):
    require_admin(request)
    try:
        gone_network = remove_network(network_id, client_address(request))
    except NetworkNotFound as error:
        raise HttpError(404, NETWORK_NOT_FOUND) from error
    except LockoutRisk as error:
        raise HttpError(400, lockout_message(error.address)) from error
    record(request, Action.NETWORK_REMOVED, rows=removed(network_snapshot(gone_network)))
    return overview(request)


@router.put("/private", auth=session_auth, response=AccessOut)
def private(request, payload: PrivateIn):
    require_admin(request)
    try:
        was_enabled = set_private_networks(payload.enabled, client_address(request))
    except LockoutRisk as error:
        raise HttpError(400, lockout_message(error.address)) from error
    record_changes(request, Action.PRIVATE_NETWORKS_CHANGED, private_snapshot(was_enabled), private_snapshot(payload.enabled))
    return overview(request)
