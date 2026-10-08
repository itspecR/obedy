REAL_IP_HEADER = "HTTP_X_REAL_IP"


def client_address(request):
    return request.META.get(REAL_IP_HEADER) or request.META.get("REMOTE_ADDR", "")
