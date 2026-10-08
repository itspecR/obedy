from accounts.models import Role
from accounts.permissions import require_roles

SUPERVISOR_ROLES = (Role.HR, Role.ADMIN)


def require_supervisor(request, message):
    return require_roles(request, SUPERVISOR_ROLES, message).account
