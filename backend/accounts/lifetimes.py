from datetime import timedelta

from accounts.models import Source

LOCAL_SESSION_LIFETIME = timedelta(hours=8)

_lifetimes = {Source.LOCAL: lambda: LOCAL_SESSION_LIFETIME}


def register_lifetime(source, provider):
    _lifetimes[source] = provider


def lifetime_for(account):
    provider = _lifetimes.get(account.source)
    return provider() if provider else LOCAL_SESSION_LIFETIME
