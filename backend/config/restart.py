import os
import signal
import threading

RESTART_DELAY_S = 1.0
CONTAINER_MAIN_PROCESS = 1


def stop_main_process():
    os.kill(CONTAINER_MAIN_PROCESS, signal.SIGTERM)


def runs_in_container():
    return os.getppid() == CONTAINER_MAIN_PROCESS


def schedule_restart():
    if runs_in_container():
        threading.Timer(RESTART_DELAY_S, stop_main_process).start()
