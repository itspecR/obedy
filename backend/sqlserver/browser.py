import socket

BROWSER_PORT = 1434
BROWSER_TIMEOUT_S = 2
REPLY_SIZE = 65535
INSTANCE_QUERY = b"\x04"
REPLY_HEADER = 3
INSTANCE_SEPARATOR = "\\"


def split_instance(host):
    server, separator, instance = host.partition(INSTANCE_SEPARATOR)
    return (server, instance) if separator and instance else (host, None)


def instance_records(reply):
    body = reply[REPLY_HEADER:].decode("ascii", errors="replace")
    for record in filter(None, body.split(";;")):
        values = record.split(";")
        yield {key.lower(): value for key, value in zip(values[::2], values[1::2], strict=False)}


def port_in_reply(reply, instance):
    for record in instance_records(reply):
        if record.get("instancename", "").lower() == instance.lower() and record.get("tcp"):
            return record["tcp"]
    return None


def ask_browser(server, instance):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as browser:
        browser.settimeout(BROWSER_TIMEOUT_S)
        browser.sendto(INSTANCE_QUERY + instance.encode("ascii") + b"\x00", (server, BROWSER_PORT))
        reply, _ = browser.recvfrom(REPLY_SIZE)
    return reply


def instance_port(server, instance):
    try:
        return port_in_reply(ask_browser(server, instance), instance)
    except (OSError, UnicodeEncodeError):
        return None


def with_instance_port(params):
    server, instance = split_instance(params.get("HOST") or "")
    if not instance:
        return params
    if params.get("PORT"):
        return {**params, "HOST": server}
    port = instance_port(server, instance)
    return {**params, "HOST": server, "PORT": port} if port else params
