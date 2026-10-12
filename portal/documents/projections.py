import json
from pathlib import Path
from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.urls import reverse
from openpyxl.utils.cell import get_column_letter

from .models import Category
from .policy import ERRORS
from .storage import private_path


def document_context(record, revision, params, mode="reader"):
    file = revision.file_revision
    base = f"/documents/{record.pk}" if mode == "reader" else f"/admin/documents/{record.pk}/draft" if mode == "draft" else f"/admin/documents/{record.pk}/revisions/{revision.number}"
    version = str(revision.pk) if mode == "reader" else str(record.edit_version) if mode == "draft" else str(revision.pk)
    query = urlencode({"v": version})
    context = {"document_category": dict(Category.choices).get(revision.payload.get("category"), ""), "file": file, "document_mode": mode}
    if not file: return context
    preview = file.preview
    context.update({"file_state": preview.get_state_display(), "file_failed": preview.state == "failed", "file_ready": preview.state == "ready", "file_limit_detail": preview.failure_detail, "file_error": ERRORS.get(preview.error_code, ERRORS["invalid"]), "download_url": f"{base}/download/?{query}", "preview_url": f"{base}/preview/?{query}", "frame_url": f"{base}/frame/?{query}", "file_notes": preview.manifest.get("notes", []), "status_url": f"{base}/status/?{query}"})
    if preview.state != "ready": return context
    manifest = preview.manifest
    def number(key, maximum):
        try: return min(max(int(params.get(key, 0)), 0), max(0, maximum - 1))
        except (ValueError, TypeError): return 0
    if manifest["kind"] == "table":
        sheets = manifest["sheets"]
        index = number("sheet", len(sheets))
        sheet = sheets[index]
        pages = Paginator(range(1, sheet["rows"] + 1), 100).get_page(params.get("cells_page"))
        path = private_path(preview.asset_prefix) / f"sheet-{index}-{pages.number - 1}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = [{"number": row, "cells": [data.get(str(row), {}).get(str(column), {"value": ""}) for column in range(1, sheet["columns"] + 1)]} for row in pages]
        context.update({"table_preview": True, "sheets": sheets, "sheet_index": index, "selected_sheet": sheet, "cell_columns": [get_column_letter(c) for c in range(1, sheet["columns"] + 1)], "cell_rows": rows, "cell_page": pages})
    else:
        pages = manifest["pages"]
        index = number("document_page", len(pages))
        page = pages[index]
        context.update({"diagram_preview": True, "diagram_pages": pages, "diagram_page": index, "viewer_payload": {"kind": manifest["kind"], "page": index + 1, "url": f"{base}/asset/{page['asset']}/?{query}"}})
    return context
