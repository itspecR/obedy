from directory.connection import BindRejected, DirectoryUnavailable, open_connection
from directory.users import find_user, is_member


class WrongPassword(Exception):
    pass


class NotAllowed(Exception):
    pass


class ServiceAccountRejected(DirectoryUnavailable):
    pass


def service_connection(config):
    try:
        return open_connection(config, config.bind_user, config.bind_password)
    except BindRejected as error:
        raise ServiceAccountRejected from error


def find_permitted_user(config, login):
    connection = service_connection(config)
    try:
        user = find_user(connection, config.base_dn, login)
        if user is None or user.disabled:
            raise NotAllowed
        if config.group_dn and not is_member(connection, user, config.group_dn):
            raise NotAllowed
        return user
    finally:
        connection.unbind()


def check_password(config, user, password):
    try:
        connection = open_connection(config, user.dn, password)
    except BindRejected as error:
        raise WrongPassword from error
    connection.unbind()


def authenticate_user(config, login, password):
    if not login or not password:
        raise WrongPassword
    user = find_permitted_user(config, login)
    check_password(config, user, password)
    return user
