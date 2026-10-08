from django.utils import timezone
from ninja.errors import HttpError
from ninja.security import APIKeyCookie

from accounts.cookies import SESSION_COOKIE
from accounts.sessions import find_active_session

PASSWORD_CHANGE_REQUIRED = "Смените пароль, чтобы продолжить"


class SessionAuth(APIKeyCookie):
    param_name = SESSION_COOKIE

    def __init__(self, allow_pending_password_change=False):
        super().__init__(csrf=False)
        self.allow_pending_password_change = allow_pending_password_change

    def authenticate(self, request, key):
        if not key:
            return None
        session = find_active_session(key, timezone.now())
        if session is None:
            return None
        if session.account.must_change_password and not self.allow_pending_password_change:
            raise HttpError(403, PASSWORD_CHANGE_REQUIRED)
        request.session_token = key
        return session


session_auth = SessionAuth()
pending_password_auth = SessionAuth(allow_pending_password_change=True)
