from django.http import HttpResponse
from django.utils import timezone
from ninja import Router, Schema, Status
from ninja.errors import HttpError

from accounts.cookies import DEVICE_COOKIE, clear_session_cookie, set_device_cookie, set_session_cookie
from accounts.credentials import DomainPassword, SamePassword, WrongCurrentPassword, change_own_password, flag_weak_password
from accounts.login import AccountLocked, InvalidCredentials, authenticate
from accounts.names import display_name
from accounts.password_policy import WeakPassword
from accounts.security import pending_password_auth
from accounts.sessions import find_active_session, revoke_session
from accounts.throttle import ServerBusy

LOGIN_FAILED = "Неверный логин или пароль. После 5 ошибок подряд вход закрывается на 15 минут"
LOCKED = (423, "Учётная запись закрыта на 15 минут")
BUSY = (503, "Сервер занят. Попробуйте ещё раз через минуту")

LOGIN_ERRORS = {
    InvalidCredentials: (401, LOGIN_FAILED),
    ServerBusy: BUSY,
}

PASSWORD_CHANGE_ERRORS = {
    WrongCurrentPassword: (400, "Текущий пароль указан неверно"),
    AccountLocked: LOCKED,
    SamePassword: (400, "Новый пароль должен отличаться от текущего"),
    DomainPassword: (400, "Пароль доменной учётной записи меняется в Windows, а не здесь"),
    ServerBusy: BUSY,
}

router = Router(tags=["Вход"])


class LoginIn(Schema):
    login: str
    password: str


class ChangePasswordIn(Schema):
    new_password: str
    current_password: str | None = None


class MeOut(Schema):
    login: str
    display_name: str
    role: str
    source: str
    must_change_password: bool
    weak_password: bool


def me_from_account(account):
    return MeOut(
        login=account.login,
        display_name=display_name(account),
        role=account.role,
        source=account.source,
        must_change_password=account.must_change_password,
        weak_password=account.weak_password,
    )


@router.post("/login", response={200: MeOut})
def login(request, payload: LoginIn, response: HttpResponse):
    now = timezone.now()
    try:
        result = authenticate(payload.login, payload.password, request.COOKIES.get(DEVICE_COOKIE), now)
    except tuple(LOGIN_ERRORS) as error:
        status, message = LOGIN_ERRORS[type(error)]
        raise HttpError(status, message) from error
    flag_weak_password(result.account, payload.password)
    session = find_active_session(result.session_token, now)
    set_session_cookie(response, result.session_token, session.expires_at)
    if result.device_token:
        set_device_cookie(response, result.device_token)
    return me_from_account(result.account)


@router.post("/logout", auth=pending_password_auth, response={204: None})
def logout(request, response: HttpResponse):
    revoke_session(request.session_token)
    clear_session_cookie(response)
    return Status(204, None)


@router.get("/me", auth=pending_password_auth, response={200: MeOut})
def me(request):
    return me_from_account(request.auth.account)


@router.post("/change-password", auth=pending_password_auth, response={200: MeOut})
def change_password(request, payload: ChangePasswordIn):
    account = request.auth.account
    try:
        change_own_password(account, payload.new_password, request.session_token, payload.current_password, timezone.now())
    except WeakPassword as error:
        raise HttpError(400, str(error)) from error
    except tuple(PASSWORD_CHANGE_ERRORS) as error:
        status, message = PASSWORD_CHANGE_ERRORS[type(error)]
        raise HttpError(status, message) from error
    return me_from_account(account)
