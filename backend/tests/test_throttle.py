import threading

import pytest

from accounts import throttle


def test_slots_are_released_after_use():
    for _ in range(throttle.PASSWORD_CHECK_SLOTS * 3):
        with throttle.password_check_slot():
            pass


def test_extra_check_waits_and_then_reports_busy(monkeypatch):
    monkeypatch.setattr(throttle, "PASSWORD_CHECK_WAIT_SECONDS", 0.1)
    release = threading.Event()
    started = threading.Barrier(throttle.PASSWORD_CHECK_SLOTS + 1)

    def hold_slot():
        with throttle.password_check_slot():
            started.wait()
            release.wait()

    holders = [threading.Thread(target=hold_slot) for _ in range(throttle.PASSWORD_CHECK_SLOTS)]
    for holder in holders:
        holder.start()
    started.wait()

    with pytest.raises(throttle.ServerBusy):
        with throttle.password_check_slot():
            pass

    release.set()
    for holder in holders:
        holder.join()
