from accounts.models import Role

UNTRACKED_ROLES = (Role.HR, Role.ADMIN)
LUNCHLESS_ROLES = (Role.ADMIN,)
LUNCH_ROLES = tuple(role for role in Role if role not in LUNCHLESS_ROLES)


def tracks_lunch_by_default(role):
    return role not in UNTRACKED_ROLES


def can_have_lunch(role):
    return role not in LUNCHLESS_ROLES
