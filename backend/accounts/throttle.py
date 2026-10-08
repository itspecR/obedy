import threading
from contextlib import contextmanager

PASSWORD_CHECK_SLOTS = 2
PASSWORD_CHECK_WAIT_SECONDS = 2

_slots = threading.BoundedSemaphore(PASSWORD_CHECK_SLOTS)


class ServerBusy(Exception):
    pass


@contextmanager
def password_check_slot():
    if not _slots.acquire(timeout=PASSWORD_CHECK_WAIT_SECONDS):
        raise ServerBusy
    try:
        yield
    finally:
        _slots.release()
