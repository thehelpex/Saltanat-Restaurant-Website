import base64
import binascii
import hmac
import os

from django.conf import settings
from django.http import HttpRequest
from rest_framework import status
from rest_framework.response import Response


def staff_actor(request: HttpRequest) -> tuple[str | None, Response | None]:
    if not settings.DEBUG and not request.is_secure():
        return None, Response(
            {"error": "The staff dashboard requires an HTTPS connection."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    expected_username = os.environ.get("STAFF_DASHBOARD_USERNAME")
    expected_password = os.environ.get("STAFF_DASHBOARD_PASSWORD")
    if not expected_username or not expected_password:
        return None, Response(
            {"error": "Staff dashboard credentials are not configured."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    authorization = request.headers.get("Authorization", "")
    scheme, _, encoded = authorization.partition(" ")
    if scheme.casefold() != "basic" or not encoded:
        return None, _unauthorized()

    try:
        decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return None, _unauthorized()

    username, separator, password = decoded.partition(":")
    username_matches = hmac.compare_digest(username, expected_username)
    password_matches = hmac.compare_digest(password, expected_password)
    if not separator or not username_matches or not password_matches:
        return None, _unauthorized()

    return username, None


def _unauthorized() -> Response:
    response = Response(
        {"error": "Valid staff dashboard credentials are required."},
        status=status.HTTP_401_UNAUTHORIZED,
    )
    response["WWW-Authenticate"] = 'Basic realm="Saltanat Staff", charset="UTF-8"'
    return response
