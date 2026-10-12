from django.contrib.auth import SESSION_KEY, logout
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.deprecation import MiddlewareMixin

from .models import User


class AccessMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            if not request.user.is_active or request.session.get("account_access_version") != request.user.access_version:
                logout(request)
        elif SESSION_KEY in request.session:
            logout(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not getattr(view_func, "login_required", True):
            return None
        api = getattr(view_func, "api_endpoint", False)
        if not request.user.is_authenticated:
            if api:
                return JsonResponse({"status": "unauthenticated", "message": "Veuillez vous connecter."}, status=401)
            # Do not copy private URLs or query strings into a public redirect.
            return redirect("login")
        if request.path.startswith("/admin/") and request.user.role != User.Role.ADMIN:
            if api:
                return JsonResponse({"status": "forbidden", "message": "Accès administrateur requis."}, status=403)
            return render(request, "core/error.html", {"error_title": "Accès réservé", "error_message": "Cette action est réservée aux administrateurs."}, status=403)


def api_endpoint(view):
    view.api_endpoint = True
    return view
