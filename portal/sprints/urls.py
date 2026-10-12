from django.urls import path
from . import views

urlpatterns = [
    path("admin/sprints/<uuid:record_id>/activate/", views.activate, name="sprint-activate"),
    path("admin/sprints/<uuid:record_id>/close/", views.close, name="sprint-close"),
]
