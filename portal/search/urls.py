from django.urls import path
from . import views

urlpatterns = [
    path("search/", views.directory, name="search"),
    path("assistant/", views.assistant, name="assistant"),
    path("assistant/query/", views.query, name="assistant-query"),
    path("assistant/source/<str:token>/", views.source, name="search-source"),
    path("admin/search/", views.administration, name="search-admin"),
    path("admin/search/preview/", views.query, {"preview": True}, name="assistant-preview-query"),
    path("admin/search/reindex/", views.reindex, name="search-reindex"),
]
