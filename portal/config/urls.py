from django.conf import settings
from django.urls import include, path

from core import views
from accounts.views import sign_in

urlpatterns = [
    path("", sign_in, name="entry"),
    path("", include("accounts.urls")),
    path("", include("knowledge.urls")),
    path("", include("sprints.urls")),
    path("", include("documents.urls")),
    path("", include("search.urls")),
    path("health/live/", views.live, name="health-live"),
    path("health/ready/", views.ready, name="health-ready"),
]
if settings.DEBUG and not settings.PRODUCTION:
    urlpatterns += [path("__preview__/applications/", views.preview, name="shell-preview")]

handler404 = "core.views.not_found"
handler500 = "core.views.server_error"
handler403 = "core.views.forbidden"
