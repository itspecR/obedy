from django.conf import settings

SESSION_COOKIE = "obedy_session"
DEVICE_COOKIE = "obedy_device"
DEVICE_COOKIE_MAX_AGE = 365 * 24 * 60 * 60


def set_session_cookie(response, token, expires_at):
    response.set_cookie(
        SESSION_COOKIE,
        token,
        expires=expires_at,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="Lax",
    )


def set_device_cookie(response, token):
    response.set_cookie(
        DEVICE_COOKIE,
        token,
        max_age=DEVICE_COOKIE_MAX_AGE,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="Lax",
    )


def clear_session_cookie(response):
    response.delete_cookie(SESSION_COOKIE, samesite="Lax")
