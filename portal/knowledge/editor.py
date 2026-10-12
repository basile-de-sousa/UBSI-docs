"""Bounded canonical editor JSON, safe HTML and exact text from one allowlist."""
from dataclasses import dataclass
from html import escape
import json
import re
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from django.core.exceptions import ValidationError


def safe_href(value):
    if not isinstance(value, str) or not value or len(value) > 2048 or re.search(r"[\s\x00-\x1f\\]", value):
        raise ValidationError("Le lien doit être une URL HTTP(S), mailto ou un chemin local valide.")
    parsed = urlsplit(value)
    if parsed.scheme in {"http", "https"} and parsed.hostname and not parsed.username and not parsed.password:
        return value
    if parsed.scheme == "mailto" and parsed.path and not parsed.netloc:
        return value
    if not parsed.scheme and (value.startswith("#") or (value.startswith("/") and not value.startswith("//"))):
        return value
    raise ValidationError("Ce type de lien n’est pas autorisé.")


@dataclass
class Document:
    json: dict
    html: str
    text: str
    sections: list


def validate_document(raw):
    try:
        if isinstance(raw, str):
            if len(raw.encode()) > 1024 * 1024:
                raise ValueError
            raw = json.loads(raw)
        if len(json.dumps(raw).encode()) > 1024 * 1024:
            raise ValueError
    except (ValueError, TypeError, RecursionError):
        raise ValidationError("Le document est invalide ou dépasse 1 Mio.") from None
    count, text_size = 0, 0
    headings = set()
    blocks = {"paragraph", "heading", "bulletList", "orderedList", "codeBlock", "table"}
    grammar = {
        "doc": blocks, "paragraph": {"text", "hardBreak"}, "heading": {"text", "hardBreak"},
        "codeBlock": {"text"}, "bulletList": {"listItem"}, "orderedList": {"listItem"},
        "listItem": {"paragraph", "bulletList", "orderedList", "codeBlock"},
        "table": {"tableRow"}, "tableRow": {"tableCell", "tableHeader"},
        "tableCell": {"paragraph"}, "tableHeader": {"paragraph"},
    }

    def visit(node, depth=0):
        nonlocal count, text_size
        count += 1
        if depth > 16 or count > 10000 or not isinstance(node, dict):
            raise ValueError
        kind = node.get("type")
        if kind not in {*grammar, "text", "hardBreak"} or set(node) - {"type", "attrs", "content", "text", "marks"}:
            raise ValueError
        attrs = node.get("attrs", {})
        if not isinstance(attrs, dict):
            raise ValueError
        canonical, html_attrs = {"type": kind}, ""
        allowed_attrs = {"heading": {"level", "id"}, "orderedList": {"start", "type"}, "codeBlock": {"language"}, "tableCell": {"colspan", "rowspan", "colwidth", "align"}, "tableHeader": {"colspan", "rowspan", "colwidth", "align"}}
        if set(attrs) - allowed_attrs.get(kind, set()):
            raise ValueError
        if kind == "text":
            value = node.get("text")
            if not isinstance(value, str) or not value or "content" in node or attrs:
                raise ValueError
            text_size += len(value)
            if text_size > 200000 or "\x00" in value:
                raise ValueError
            canonical["text"] = value
            html = escape(value)
            marks = node.get("marks", [])
            if not isinstance(marks, list) or len(marks) > 3:
                raise ValueError
            clean_marks, seen = [], set()
            for mark in marks:
                if not isinstance(mark, dict) or set(mark) - {"type", "attrs"} or mark.get("type") not in {"bold", "italic", "link"} or mark["type"] in seen:
                    raise ValueError
                seen.add(mark["type"])
                if mark["type"] == "link":
                    values = mark.get("attrs", {})
                    if not isinstance(values, dict) or set(values) - {"href", "target", "rel", "class", "title"}:
                        raise ValueError
                    href = safe_href(values.get("href"))
                    clean_marks.append({"type": "link", "attrs": {"href": href, "target": None, "rel": "noopener noreferrer", "class": None}})
                    html = f'<a href="{escape(href, quote=True)}" rel="noopener noreferrer">{html}</a>'
                else:
                    if mark.get("attrs"):
                        raise ValueError
                    clean_marks.append({"type": mark["type"]})
                    tag = "strong" if mark["type"] == "bold" else "em"
                    html = f"<{tag}>{html}</{tag}>"
            if clean_marks:
                canonical["marks"] = clean_marks
            return canonical, html, value
        if "text" in node or node.get("marks"):
            raise ValueError
        if kind == "hardBreak":
            if attrs or node.get("content"):
                raise ValueError
            return canonical, "<br>", "\n"
        children = node.get("content", [])
        if not isinstance(children, list) or any(not isinstance(child, dict) or child.get("type") not in grammar[kind] for child in children):
            raise ValueError
        if kind not in {"paragraph", "heading", "codeBlock", "doc"} and not children:
            raise ValueError
        if kind == "listItem" and children[0]["type"] != "paragraph":
            raise ValueError
        if kind == "heading":
            level = attrs.get("level", 2)
            if type(level) is not int or level not in {2, 3, 4}:
                raise ValueError
            identifier = str(UUID(str(attrs["id"]))) if attrs.get("id") else str(uuid4())
            if identifier in headings:
                raise ValidationError("Deux sections portent le même identifiant. Dupliquez-les depuis l’éditeur.")
            headings.add(identifier)
            canonical["attrs"] = {"level": level, "id": identifier}
            html_attrs = f' id="section-{identifier}"'
        if kind == "orderedList":
            start = attrs.get("start", 1)
            if type(start) is not int or not 1 <= start <= 100000 or attrs.get("type") not in {None, "1"}:
                raise ValueError
            canonical["attrs"] = {"start": start}
            html_attrs = f' start="{start}"'
        if kind == "codeBlock":
            if attrs.get("language") is not None or any(child.get("marks") for child in children):
                raise ValueError
            canonical["attrs"] = {"language": None}
        if kind in {"tableCell", "tableHeader"}:
            if attrs.get("colspan", 1) != 1 or attrs.get("rowspan", 1) != 1 or attrs.get("colwidth") is not None or attrs.get("align") is not None:
                raise ValidationError("Les tableaux utilisent des cellules simples, sans fusion ni largeur imposée.")
            canonical["attrs"] = {"colspan": 1, "rowspan": 1, "colwidth": None}
        if kind == "table":
            widths = [len(row.get("content", [])) for row in children]
            if len(children) > 50 or not widths or not 1 <= widths[0] <= 20 or len(set(widths)) != 1:
                raise ValidationError("Un tableau doit être rectangulaire, avec au plus 50 lignes et 20 colonnes.")
        parts = [visit(child, depth + 1) for child in children]
        if parts:
            canonical["content"] = [part[0] for part in parts]
        inner = "".join(part[1] for part in parts)
        separator = "" if kind in {"paragraph", "heading", "codeBlock"} else ("\t" if kind == "tableRow" else "\n")
        text = separator.join(part[2] for part in parts)
        tags = {"doc": "", "paragraph": "p", "heading": f'h{attrs.get("level", 2)}', "bulletList": "ul", "orderedList": "ol", "listItem": "li", "table": "table", "tableRow": "tr", "tableCell": "td", "tableHeader": "th"}
        if kind == "codeBlock":
            html = f"<pre><code>{inner}</code></pre>"
        elif kind == "table":
            html = f'<div class="table-scroll"><table><tbody>{inner}</tbody></table></div>'
        else:
            tag = tags[kind]
            html = f"<{tag}{html_attrs}>{inner}</{tag}>" if tag else inner
        return canonical, html, text

    try:
        if not isinstance(raw, dict) or raw.get("type") != "doc":
            raise ValueError
        canonical, html, text = visit(raw)
        def plain(node):
            if node["type"] == "text":
                return node["text"]
            if node["type"] == "hardBreak":
                return "\n"
            separator = "" if node["type"] in {"paragraph", "heading", "codeBlock"} else ("\t" if node["type"] == "tableRow" else "\n")
            return separator.join(plain(child) for child in node.get("content", []))
        sections, current = [], {"id": "", "title": "", "text": ""}
        for node in canonical.get("content", []):
            node_text = plain(node)
            if node["type"] == "heading":
                if current["text"]:
                    sections.append(current)
                current = {"id": node["attrs"]["id"], "title": node_text[:200], "text": node_text}
            else:
                current["text"] += ("\n" if current["text"] else "") + node_text
        if current["text"]:
            sections.append(current)
        return Document(canonical, html, text, sections)
    except (ValueError, TypeError, KeyError, RecursionError):
        raise ValidationError("Le document contient une structure, un attribut ou un format non autorisé.") from None


def specification_template():
    content = []
    for title in ["Contexte", "Objectif", "Périmètre", "Règles fonctionnelles", "Flux de données liés", "Critères d’acceptation", "Questions ouvertes"]:
        content.extend([{"type": "heading", "attrs": {"level": 2, "id": str(uuid4())}, "content": [{"type": "text", "text": title}]}, {"type": "paragraph"}])
    return {"type": "doc", "content": content}
