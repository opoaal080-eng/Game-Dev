class PrivateContentMiddleware:
    """No private portal pages or downloads should be cached by shared intermediaries."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not request.path.startswith("/static/"):
            response["Cache-Control"] = "private, no-store, max-age=0"
            response["Pragma"] = "no-cache"
        return response


class NativePagesCORSMiddleware:
    """Allow our public GitHub Pages *client*, not public access to private data.

    CORS only enables requests from a known browser origin. Every API read/write
    still requires a valid bearer token and server-side permission checks.
    """
    allowed_origins = frozenset({
        "https://opoaal080-eng.github.io",
    })
    allowed_methods = "GET, POST, PUT, PATCH, OPTIONS"
    allowed_headers = "Authorization, Content-Type, Accept"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/v1/"):
            return self.get_response(request)

        from django.http import HttpResponse
        from django.utils.cache import patch_vary_headers

        origin = request.headers.get("Origin", "")
        allowed = origin in self.allowed_origins
        if request.method == "OPTIONS" and allowed:
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)
        if allowed:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Methods"] = self.allowed_methods
            response["Access-Control-Allow-Headers"] = self.allowed_headers
            response["Access-Control-Max-Age"] = "600"
        patch_vary_headers(response, ("Origin",))
        return response
