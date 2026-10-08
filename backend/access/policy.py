import time
from dataclasses import dataclass

from access.models import POLICY_ID, AccessPolicy, AllowedNetwork
from access.networks import is_allowed, parse_network

CACHE_SECONDS = 5


@dataclass(frozen=True)
class Policy:
    allow_private: bool
    networks: tuple

    def allows(self, address):
        return is_allowed(address, self.allow_private, self.networks)


_cache = {"policy": None, "loaded_at": 0.0}


def stored_policy():
    return AccessPolicy.objects.get_or_create(pk=POLICY_ID)[0]


def load_policy():
    networks = tuple(parse_network(value) for value in AllowedNetwork.objects.values_list("network", flat=True))
    return Policy(stored_policy().allow_private_networks, networks)


def current_policy():
    now = time.monotonic()
    if _cache["policy"] is None or now - _cache["loaded_at"] >= CACHE_SECONDS:
        _cache["policy"] = load_policy()
        _cache["loaded_at"] = now
    return _cache["policy"]


def forget_policy():
    _cache["policy"] = None
