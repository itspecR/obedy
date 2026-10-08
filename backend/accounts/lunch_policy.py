from accounts.models import Role

UNTRACKED_ROLES = (Role.HR, Role.ADMIN)


def tracks_lunch_by_default(role):
    return role not in UNTRACKED_ROLES
