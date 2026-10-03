from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.cache import patch_vary_headers


class ApiCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method == "OPTIONS":
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        origin = request.headers.get("Origin")
        if origin in settings.CORS_ALLOWED_ORIGINS:
            response["Access-Control-Allow-Origin"] = origin
            patch_vary_headers(response, ("Origin",))
            if request.method == "OPTIONS":
                response["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
                response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
                response["Access-Control-Max-Age"] = "600"
        return response
