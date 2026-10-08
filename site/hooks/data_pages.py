"""MkDocs hook: turn data/*.csv into site pages at build time.

Nothing generated here is written to the repo. The data stays in data/,
the written content in docs/, and this hook is the only bridge between them.
"""
from __future__ import annotations

import sys
from pathlib import Path

from mkdocs.exceptions import PluginError
from mkdocs.structure.files import File

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from ubsi_data import load, validate  # noqa: E402

PAGES_DIR = "referentiels"
APPS_DIR = "applications"


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _table(header: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_Aucune ligne pour l'instant._\n"
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(_cell(c) for c in r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def _app_link(code: str, depth: int) -> str:
    return f"[{code}]({'../' * depth}{APPS_DIR}/{code.lower()}.md)"


def _render_cell(ds, row, col, depth) -> str:
    opts = ds.columns[col]
    vals = ds.values(row, col)
    if opts.get("ref") and opts["ref"].startswith("applications."):
        vals = [_app_link(v, depth) for v in vals]
    return ", ".join(vals)


def _dataset_page(ds) -> str:
    cols = list(ds.columns)
    rows = [[_render_cell(ds, r, c, 1) for c in cols] for r in ds.rows]
    return (
        f"# {ds.title}\n\n{ds.description}\n\n"
        f"Source : `data/{ds.file.name}` · "
        f"[Télécharger le CSV](../data/{ds.file.name})\n\n"
        f"{_table(cols, rows)}\n"
        "!!! note \"Modifier ces données\"\n"
        f"    Cette page est générée. Pour la changer, modifiez `data/{ds.file.name}` "
        "via une pull request (voir [Contribuer](../contribuer.md)).\n"
    )


def _app_page(app, ds) -> str:
    code = app["code"]
    d, f = ds["donnees"], ds["flux"]

    def data_rows(pred):
        return [[r["id"], r["nom"], r["categorie"], _app_link(r["app_proprietaire"], 1)]
                for r in d.rows if pred(r)]

    owned = data_rows(lambda r: r["app_proprietaire"] == code)
    copied = data_rows(lambda r: code in d.values(r, "apps_copie"))
    consulted = data_rows(lambda r: code in d.values(r, "apps_consultation"))
    transferred = data_rows(lambda r: code in d.values(r, "apps_transfert"))
    dh = ["id", "nom", "catégorie", "propriétaire"]

    def flux_rows(col):
        other = "app_cible" if col == "app_source" else "app_source"
        return [[r["id"], _app_link(r[other], 1), ", ".join(f.values(r, "donnees")),
                 r["synchronisme"], r["mode"], r["scenario"]]
                for r in f.rows if r[col] == code]

    fh = ["id", "application", "données", "synchronisme", "mode", "scénario"]
    return (
        f"# {app['nom']} ({code})\n\n{app.get('description', '')}\n\n"
        f"Type : **{app['type']}**\n\n"
        f"## Données dont l'application est propriétaire\n\n{_table(dh, owned)}\n"
        f"## Données copiées\n\n{_table(dh, copied)}\n"
        f"## Données consultées\n\n{_table(dh, consulted)}\n"
        f"## Données reçues par transfert\n\n{_table(dh, transferred)}\n"
        f"## Flux sortants\n\n{_table(fh, flux_rows('app_source'))}\n"
        f"## Flux entrants\n\n{_table(fh, flux_rows('app_cible'))}\n"
    )


def _apps_index(apps) -> str:
    rows = [[f"[{a['nom']}]({a['code'].lower()}.md)", a["code"], a["type"], a.get("description", "")]
            for a in apps.rows]
    return ("# Applications\n\nUne page par application, générée depuis `data/`.\n\n"
            + _table(["application", "code", "type", "description"], rows))


def _front(path: Path, key: str) -> str:
    """Read 'status' from a spec frontmatter or an ADR 'Status:' line, and the H1 title."""
    text = path.read_text(encoding="utf-8")
    if key == "title":
        return next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), path.stem)
    for line in text.splitlines():
        low = line.lower()
        if low.startswith("status:"):
            return line.split(":", 1)[1].split(" - ")[0].strip()
    return ""


def _decisions_index(docs_dir: Path, sub: str, title: str, intro: str) -> str:
    rows = [[f"[{_front(p, 'title')}]({p.name})", _front(p, "status")]
            for p in sorted((docs_dir / sub).glob("[0-9]*.md"))]
    return f"# {title}\n\n{intro}\n\n" + _table(["titre", "statut"], rows)


def on_files(files, config):
    datasets = load()
    errors = validate(datasets)
    if errors:
        raise PluginError("Invalid data in data/:\n  " + "\n  ".join(errors))

    def add(uri: str, content: str | bytes):
        files.append(File.generated(config, uri, content=content))

    for ds in datasets.values():
        add(f"{PAGES_DIR}/{ds.name}.md", _dataset_page(ds))
        add(f"data/{ds.file.name}", ds.file.read_bytes())

    apps = datasets["applications"]
    add(f"{APPS_DIR}/index.md", _apps_index(apps))
    for app in apps.rows:
        add(f"{APPS_DIR}/{app['code'].lower()}.md", _app_page(app, datasets))

    docs_dir = Path(config["docs_dir"])
    add("adr/index.md", _decisions_index(
        docs_dir, "adr", "Décisions d'architecture (ADR)",
        "Chaque décision structurante est tracée dans `docs/adr/`."))
    add("specs/index.md", _decisions_index(
        docs_dir, "specs", "Specs",
        "Specs de sprint et de fonctionnalités, dans `docs/specs/`."))
    return files
