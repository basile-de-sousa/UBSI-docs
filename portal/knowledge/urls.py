from django.urls import path

from . import views
from .models import Kind

urlpatterns = [
    path("documents/", views.reader_list, {"kind": Kind.DOCUMENT}, name="documents"),
    path("documents/<uuid:record_id>/", views.reader_detail, {"kind": Kind.DOCUMENT}, name="document-detail"),
    path("applications/", views.reader_list, {"kind": Kind.APPLICATION}, name="applications"),
    path("applications/<uuid:record_id>/", views.reader_detail, {"kind": Kind.APPLICATION}, name="application-detail"),
    path("specifications/", views.reader_list, {"kind": Kind.SPECIFICATION}, name="specifications"),
    path("specifications/<uuid:record_id>/", views.reader_detail, {"kind": Kind.SPECIFICATION}, name="specification-detail"),
    path("faq/", views.reader_list, {"kind": Kind.FAQ}, name="faq"),
    path("faq/<uuid:record_id>/", views.reader_detail, {"kind": Kind.FAQ}, name="faq-detail"),
    path("epics/", views.reader_list, {"kind": Kind.EPIC}, name="epics"),
    path("epics/<uuid:record_id>/", views.reader_detail, {"kind": Kind.EPIC}, name="epic-detail"),
    path("stories/", views.reader_list, {"kind": Kind.STORY}, name="stories"),
    path("stories/<uuid:record_id>/", views.reader_detail, {"kind": Kind.STORY}, name="story-detail"),
    path("sprints/", views.reader_list, {"kind": Kind.SPRINT}, name="sprints"),
    path("sprints/<uuid:record_id>/", views.reader_detail, {"kind": Kind.SPRINT}, name="sprint-detail"),
    path("admin/knowledge/", views.directory, name="knowledge-admin"),
    path("admin/knowledge/import-applications/", views.import_directory, name="knowledge-import"),
    path("admin/knowledge/new/<str:kind>/", views.create, name="knowledge-create"),
    path("admin/knowledge/<uuid:record_id>/", views.edit, name="knowledge-edit"),
    path("admin/knowledge/<uuid:record_id>/begin/", views.begin, name="knowledge-begin"),
    path("admin/knowledge/<uuid:record_id>/preview/", views.preview, name="knowledge-preview"),
    path("admin/knowledge/<uuid:record_id>/publish/", views.publish, name="knowledge-publish"),
    path("admin/knowledge/<uuid:record_id>/history/", views.history, name="knowledge-history"),
    path("admin/knowledge/<uuid:record_id>/history/<int:number>/", views.history, name="knowledge-revision"),
    path("admin/knowledge/<uuid:record_id>/restore/<int:number>/", views.restore, name="knowledge-restore"),
    path("admin/knowledge/<uuid:record_id>/archive/", views.archive_or_discard, {"operation": "archive"}, name="knowledge-archive"),
    path("admin/knowledge/<uuid:record_id>/discard/", views.archive_or_discard, {"operation": "discard"}, name="knowledge-discard"),
]
