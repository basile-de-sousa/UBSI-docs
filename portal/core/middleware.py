from ipaddress import ip_address
from django.conf import settings


class TrustedProxyMiddleware:
    """Accept overwritten forwarding headers only from configured proxy peers."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            peer = ip_address(request.META.get("REMOTE_ADDR", ""))
            trusted = any(peer in network for network in settings.TRUSTED_PROXY_NETWORKS)
        except ValueError:
            trusted = False
        if trusted:
            try:
                # The edge must overwrite, rather than append, this single address.
                source = ip_address(request.META.get("HTTP_X_FORWARDED_FOR", ""))
                request.META["REMOTE_ADDR"] = str(source)
            except ValueError:
                pass
            if request.META.get("HTTP_X_FORWARDED_PROTO") not in {"http", "https"}:
                request.META.pop("HTTP_X_FORWARDED_PROTO", None)
        else:
            request.META.pop("HTTP_X_FORWARDED_FOR", None)
            request.META.pop("HTTP_X_FORWARDED_PROTO", None)
        return self.get_response(request)


class ResponsePolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not getattr(response, "document_frame", False):
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; script-src 'self'; style-src 'self'; "
                "img-src 'self'; font-src 'self'; connect-src 'self'; "
                "base-uri 'none'; object-src 'none'; frame-src 'self'; frame-ancestors 'none'; form-action 'self'"
            )
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store, private"
        match = getattr(request, "resolver_match", None)
        if match and match.url_name in {"invitation-exchange", "reset-exchange"}:
            # Bearer URLs redirect to clean form URLs. Forms keep same-origin:
            # WebKit can send Origin: null after no-referrer, which CSRF rejects.
            response.headers["Referrer-Policy"] = "no-referrer"
        return response
