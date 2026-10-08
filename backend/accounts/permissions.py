from ninja.errors import HttpError

from accounts.models import Role


def require_roles(request, roles, message="Недостаточно прав для этого действия"):
    if request.auth.account.role not in roles:
        raise HttpError(403, message)
    return request.auth


def require_admin(request):
    return require_roles(request, (Role.ADMIN,), "Раздел доступен только администратору")
