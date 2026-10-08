import ssl


class InvalidCertificate(ValueError):
    pass


def checked_certificate(pem):
    text = (pem or "").strip()
    if not text:
        return ""
    try:
        ssl.create_default_context(cadata=text)
    except (ssl.SSLError, ValueError) as error:
        raise InvalidCertificate from error
    return text
