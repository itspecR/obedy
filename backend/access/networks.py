import ipaddress

PRIVATE_RANGES = ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
LOOPBACK_RANGES = ("127.0.0.0/8", "::1/128")

PRIVATE_NETWORKS = tuple(ipaddress.ip_network(item) for item in PRIVATE_RANGES)
LOOPBACK_NETWORKS = tuple(ipaddress.ip_network(item) for item in LOOPBACK_RANGES)


class InvalidNetwork(ValueError):
    pass


def parse_network(text):
    try:
        return ipaddress.ip_network((text or "").strip(), strict=False)
    except ValueError as error:
        raise InvalidNetwork from error


def parse_address(text):
    try:
        return ipaddress.ip_address((text or "").strip())
    except ValueError:
        return None


def contains(networks, address):
    return any(address.version == network.version and address in network for network in networks)


def is_allowed(text, allow_private, networks):
    address = parse_address(text)
    if address is None:
        return False
    if contains(LOOPBACK_NETWORKS, address):
        return True
    if allow_private and contains(PRIVATE_NETWORKS, address):
        return True
    return contains(networks, address)
