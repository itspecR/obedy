import logging

from django.conf import settings
from django.db import connection
from django.db.utils import DatabaseError, IntegrityError
from ninja import NinjaAPI, Schema, Status
from ninja.errors import AuthenticationError

from access.api import router as access_router
from accounts.api import router as auth_router
from directory.api import router as directory_router
from journal.api import router as journal_router
from lunches.api import router as lunch_router
from staff.api import router as staff_router

logger = logging.getLogger(__name__)

api = NinjaAPI(
    title="Обеды",
    docs_url="/docs" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)


class HealthOut(Schema):
    status: str
    database: str


def database_is_available():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except DatabaseError:
        return False


@api.get("/health", response={200: HealthOut, 503: HealthOut})
def health(request):
    if database_is_available():
        return Status(200, HealthOut(status="ok", database="ok"))
    return Status(503, HealthOut(status="error", database="unavailable"))


@api.exception_handler(AuthenticationError)
def not_authenticated(request, exc):
    return api.create_response(request, {"detail": "Войдите в систему"}, status=401)


@api.exception_handler(IntegrityError)
def changed_concurrently(request, exc):
    return api.create_response(request, {"detail": "Данные только что изменились в другом окне. Обновите страницу и повторите"}, status=409)


@api.exception_handler(Exception)
def server_error(request, exc):
    logger.exception("Ошибка сервера: %s %s", request.method, request.path)
    return api.create_response(request, {"detail": "На сервере произошла ошибка. Попробуйте ещё раз или сообщите администратору"}, status=500)


api.add_router("/auth", auth_router)
api.add_router("/access", access_router)
api.add_router("/directory", directory_router)
api.add_router("/staff", staff_router)
api.add_router("/lunch", lunch_router)
api.add_router("/journal", journal_router)
