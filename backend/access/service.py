from django.db import IntegrityError, transaction

from access.models import AllowedNetwork
from access.networks import parse_network
from access.policy import Policy, forget_policy, load_policy, stored_policy


class DuplicateNetwork(Exception):
    pass


class LockoutRisk(Exception):
    def __init__(self, address):
        super().__init__(address)
        self.address = address


class NetworkNotFound(Exception):
    pass


def guard(next_policy, keep_address):
    if keep_address is not None and not next_policy.allows(keep_address):
        raise LockoutRisk(keep_address)


def add_network(text, note=""):
    network = str(parse_network(text))
    try:
        with transaction.atomic():
            created = AllowedNetwork.objects.create(network=network, note=note.strip())
    except IntegrityError as error:
        raise DuplicateNetwork from error
    forget_policy()
    return created


@transaction.atomic
def remove_network(network_id, keep_address):
    target = AllowedNetwork.objects.select_for_update().filter(pk=network_id).first()
    if target is None:
        raise NetworkNotFound
    current = load_policy()
    remaining = tuple(item for item in current.networks if str(item) != target.network)
    guard(Policy(current.allow_private, remaining), keep_address)
    target.delete()
    forget_policy()
    return target


@transaction.atomic
def set_private_networks(enabled, keep_address):
    policy = stored_policy()
    guard(Policy(enabled, load_policy().networks), keep_address)
    was_enabled = policy.allow_private_networks
    policy.allow_private_networks = enabled
    policy.save(update_fields=["allow_private_networks"])
    forget_policy()
    return was_enabled
