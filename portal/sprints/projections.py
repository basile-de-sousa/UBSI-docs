from django.core.paginator import Paginator

from knowledge.models import Kind, Relation, State
from knowledge.projections import canonical_url
from .forms import SprintMemberFilters
from .services import assigned_stories


def sprint_context(record, query, admin=False):
    filters = SprintMemberFilters(query)
    valid = filters.is_valid()
    snapshot = getattr(record, "closure", None)
    rows = snapshot.rows.select_related("story", "epic", "responsible").prefetch_related("applications__application") if snapshot else assigned_stories(record).prefetch_related("current_revision__relations__target__current_revision")
    if not valid:
        rows = rows.none()
    elif snapshot:
        # Hidden stories must not reveal their old application/epic membership through filters.
        if filters.cleaned_data["application"]:
            rows = rows.filter(applications__application=filters.cleaned_data["application"], story__state=State.PUBLISHED).distinct()
        if filters.cleaned_data["epic"]:
            rows = rows.filter(epic=filters.cleaned_data["epic"], story__state=State.PUBLISHED)
    else:
        for key in ["application", "epic"]:
            if filters.cleaned_data[key]:
                rows = rows.filter(current_revision__relations__kind=key, current_revision__relations__target=filters.cleaned_data[key]).distinct()
    page = Paginator(rows.order_by("reference"), 25).get_page(query.get("page"))
    projected = []
    for item in page:
        if snapshot:
            visible = admin or item.story.state == State.PUBLISHED
            row = {"available": visible}
            if visible:
                row.update(reference=item.reference, title=item.title, url=f"/admin/knowledge/{item.story_id}/" if admin else canonical_url(item.story), progress=item.get_work_state_display(), owner=item.responsible_name, epic=item.epic_title if admin or item.epic.state == State.PUBLISHED else "Epic indisponible", applications=[app.reference if admin or app.application.state == State.PUBLISHED else "Application indisponible" for app in item.applications.all()])
        else:
            revision = item.current_revision
            revision.record = item
            links = list(revision.relations.all())
            epic = next(link.target for link in links if link.kind == Relation.EPIC)
            row = {"available": True, "reference": item.reference, "title": revision.title, "url": canonical_url(item), "progress": revision.progress_label, "owner": revision.responsible.display_name if revision.responsible else "", "epic": epic.current_revision.title, "applications": [link.target.display_reference for link in links if link.kind == Relation.APPLICATION]}
        projected.append(row)
    return {"sprint_snapshot": snapshot, "sprint_rows": projected, "sprint_page": page, "sprint_filters": filters, "sprint_filter_query": "&".join(f"{key}={filters.cleaned_data[key].pk}" for key in ["application", "epic"] if valid and filters.cleaned_data.get(key)), "snapshot_admin": admin}
