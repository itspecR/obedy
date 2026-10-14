from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpResponse, JsonResponse

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
FORM_TYPES = {"application/x-www-form-urlencoded", "multipart/form-data", "text/plain"}


class SameOriginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in UNSAFE_METHODS and not self.is_same_origin(request):
            return JsonResponse({"detail": "Запрос отклонён: неверный источник"}, status=403)
        return self.get_response(request)

    @staticmethod
    def is_same_origin(request):
        source = request.headers.get("Origin") or request.headers.get("Referer")
        if not source:
            return request.content_type not in FORM_TYPES
        parts = urlsplit(source)
        return parts.scheme == request.scheme and parts.netloc == request.get_host()


SETUP_OPEN_PATHS = ("/api/setup/", "/api/health")
ACCESS_CHECK_PATH = "/api/access/check"
NOT_CONFIGURED = {"detail": "База данных ещё не подключена. Откройте сайт и подключите базу", "setup": True}


class SetupGateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DATABASE_CONFIGURED:
            return self.get_response(request)
        if request.path == ACCESS_CHECK_PATH:
            return HttpResponse(status=204)
        if request.path.startswith("/api/") and not request.path.startswith(SETUP_OPEN_PATHS):
            return JsonResponse(NOT_CONFIGURED, status=503)
        return self.get_response(request)
