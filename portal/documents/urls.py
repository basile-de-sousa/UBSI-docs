from django.urls import path
from . import views

urlpatterns = [
    path("admin/documents/<uuid:document_id>/upload/", views.upload, name="document-upload"),
    path("admin/documents/<uuid:document_id>/retry/", views.retry, name="document-retry"),
]
for base, mode in [("documents/<uuid:document_id>", "reader"), ("admin/documents/<uuid:document_id>/draft", "draft"), ("admin/documents/<uuid:document_id>/revisions/<int:revision>", "history")]:
    for suffix, view in [("preview", views.preview), ("download", views.download), ("frame", views.frame), ("status", views.status)]:
        urlpatterns.append(path(f"{base}/{suffix}/", view, {"mode": mode}))
    urlpatterns.append(path(f"{base}/asset/<str:asset_name>/", views.asset, {"mode": mode}))
urlpatterns.append(path("admin/documents/<uuid:document_id>/revisions/<int:revision>/", views.preview, {"mode": "history"}))
