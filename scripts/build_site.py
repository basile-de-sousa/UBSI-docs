"""Build the interim link portal (SPEC-002) into an output directory.

Reads site/liens.yml, validates it against data/applications.csv and writes
<out>/liens.json next to a copy of site/index.html. Exits non-zero on any
validation error so the previously deployed page stays online.

Usage: python scripts/build_site.py [out_dir]   (default: _site)
"""

import csv
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "site" / "liens.yml"
STATUSES = {"valide", "brouillon", "obsolete"}
LINK_KEYS = {"nom", "url", "description", "equipes", "statut", "maj"}


def load_teams() -> dict[str, str]:
    with open(ROOT / "data" / "applications.csv", encoding="utf-8-sig", newline="") as f:
        return {row["code"].strip(): row["nom"].strip() for row in csv.DictReader(f)}


def validate(doc, teams: dict[str, str]) -> list[str]:
    errors: list[str] = []
    if not isinstance(doc, dict) or not isinstance(doc.get("sections"), list):
        return ["the file must contain a 'sections' list"]
    for si, section in enumerate(doc["sections"], 1):
        where = f"section {si}"
        if not isinstance(section, dict) or not str(section.get("titre") or "").strip():
            errors.append(f"{where}: missing 'titre'")
            continue
        where = f"section '{section['titre']}'"
        links = section.get("liens") or []
        if not isinstance(links, list):
            errors.append(f"{where}: 'liens' must be a list")
            continue
        for li, link in enumerate(links, 1):
            at = f"{where}, link {li}"
            if not isinstance(link, dict):
                errors.append(f"{at}: must be a block of fields")
                continue
            unknown = set(link) - LINK_KEYS
            if unknown:
                errors.append(f"{at}: unknown field(s) {sorted(unknown)}")
            if not str(link.get("nom") or "").strip():
                errors.append(f"{at}: missing 'nom'")
            url = link.get("url")
            if url and not str(url).startswith(("https://", "http://")):
                errors.append(f"{at}: url must start with https://")
            status = link.get("statut", "valide")
            if status not in STATUSES:
                errors.append(f"{at}: statut must be one of {sorted(STATUSES)}")
            codes = link.get("equipes") or []
            if not isinstance(codes, list):
                errors.append(f"{at}: equipes must be a list, e.g. [BKG, PLA]")
            else:
                for code in codes:
                    if code not in teams:
                        errors.append(f"{at}: unknown team code '{code}'")
            if "maj" in link:
                try:
                    dt.date.fromisoformat(str(link["maj"]))
                except ValueError:
                    errors.append(f"{at}: maj must be a date YYYY-MM-DD")
    return errors


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site"
    teams = load_teams()
    try:
        doc = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"site/liens.yml is not valid YAML:\n{exc}", file=sys.stderr)
        return 1
    errors = validate(doc, teams)
    if errors:
        print("site/liens.yml has errors:", *errors, sep="\n- ", file=sys.stderr)
        return 1

    sections = []
    for section in doc["sections"]:
        links = []
        for link in section.get("liens") or []:
            links.append({
                "nom": str(link["nom"]).strip(),
                "url": str(link.get("url") or "").strip(),
                "description": str(link.get("description") or "").strip(),
                "equipes": link.get("equipes") or [],
                "statut": link.get("statut", "valide"),
                "maj": str(link["maj"]) if "maj" in link else "",
            })
        sections.append({
            "titre": str(section["titre"]).strip(),
            "description": str(section.get("description") or "").strip(),
            "liens": links,
        })

    payload = {
        "annonce": str(doc.get("annonce") or "").strip(),
        "equipes": teams,
        "sections": sections,
        "publie": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "liens.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    shutil.copy(ROOT / "site" / "index.html", out / "index.html")
    count = sum(len(s["liens"]) for s in sections)
    print(f"Built {out} with {len(sections)} sections and {count} links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
