"""Load and validate the CSV datasets in data/ against data/schema.yaml.

Shared by scripts/validate.py (CLI, CI) and site/hooks/data_pages.py (site build).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SCHEMA_FILE = DATA_DIR / "schema.yaml"
SEP = ";"


@dataclass
class Dataset:
    name: str
    file: Path
    title: str
    description: str
    key: str
    columns: dict
    rows: list[dict] = field(default_factory=list)
    header: list[str] | None = None  # None when the file is missing

    def values(self, row: dict, col: str) -> list[str]:
        """Cell value as a list (split on ';' for multi columns, empty list if blank)."""
        raw = (row.get(col) or "").strip()
        if not raw:
            return []
        if self.columns.get(col, {}).get("multi"):
            return [v.strip() for v in raw.split(SEP) if v.strip()]
        return [raw]


def load(data_dir: Path = DATA_DIR) -> dict[str, Dataset]:
    schema = yaml.safe_load((data_dir / "schema.yaml").read_text(encoding="utf-8"))
    datasets: dict[str, Dataset] = {}
    for name, spec in schema["datasets"].items():
        path = data_dir / spec["file"]
        ds = Dataset(
            name=name,
            file=path,
            title=spec.get("title", name),
            description=(spec.get("description") or "").strip(),
            key=spec["key"],
            columns={c: (o or {}) for c, o in spec["columns"].items()},
        )
        if path.exists():
            with path.open(encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                ds.header = reader.fieldnames or []
                ds.rows = [
                    {k: (v or "").strip() for k, v in r.items()}
                    for r in reader
                    if any((v or "").strip() for v in r.values())
                ]
        else:
            ds.header = None
        datasets[name] = ds
    return datasets


def validate(datasets: dict[str, Dataset]) -> list[str]:
    """Return a list of human-readable errors (empty list = valid)."""
    errors: list[str] = []
    for ds in datasets.values():
        where = f"data/{ds.file.name}"
        if ds.header is None:
            errors.append(f"{where}: file missing")
            continue
        expected = list(ds.columns)
        if ds.header != expected:
            errors.append(f"{where}: header must be {','.join(expected)} (got {','.join(ds.header)})")
            continue
        seen: dict[str, set] = {c: set() for c, o in ds.columns.items() if o.get("unique")}
        for i, row in enumerate(ds.rows, start=2):  # line 1 is the header
            loc = f"{where}:{i}"
            for col, opts in ds.columns.items():
                vals = ds.values(row, col)
                if opts.get("required") and not vals:
                    errors.append(f"{loc}: '{col}' is required")
                if opts.get("unique") and vals:
                    if vals[0] in seen[col]:
                        errors.append(f"{loc}: duplicate {col} '{vals[0]}'")
                    seen[col].add(vals[0])
                for v in vals:
                    if "enum" in opts and v not in opts["enum"]:
                        errors.append(f"{loc}: '{col}' = '{v}' not in {opts['enum']}")
                    if "ref" in opts:
                        ref_ds, ref_col = opts["ref"].split(".")
                        target = datasets[ref_ds]
                        if v not in {r.get(ref_col) for r in target.rows}:
                            errors.append(f"{loc}: '{col}' = '{v}' unknown in data/{target.file.name} ({ref_col})")
    return errors
