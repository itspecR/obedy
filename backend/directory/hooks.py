import logging
from datetime import timedelta

from accounts.lifetimes import register_lifetime
from accounts.models import Source
from accounts.verification import VerifierUnavailable, register_newcomer_admitter, register_verifier
from directory.authentication import NotAllowed, WrongPassword, authenticate_user
from directory.config import current_config
from directory.connection import DirectoryUnavailable
from directory.provisioning import save_account

logger = logging.getLogger(__name__)


def domain_user(login, password):
    config = current_config()
    if not config.ready:
        return None
    try:
        return authenticate_user(config, login, password)
    except (WrongPassword, NotAllowed):
        return None
    except DirectoryUnavailable as error:
        logger.warning("Контроллер домена недоступен при входе: %s", type(error.__cause__ or error).__name__)
        raise VerifierUnavailable from error


def verify_domain_account(account, password):
    user = domain_user(account.login, password)
    if user is None:
        return False
    save_account(user)
    account.refresh_from_db()
    return True


def admit_domain_user(login, password):
    user = domain_user(login, password)
    return save_account(user) if user is not None else None


def domain_session_lifetime():
    return timedelta(days=current_config().session_days)


def register_domain_hooks():
    register_verifier(Source.DOMAIN, verify_domain_account)
    register_newcomer_admitter(admit_domain_user)
    register_lifetime(Source.DOMAIN, domain_session_lifetime)
