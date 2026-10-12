"""Acquire hash-verified M0 assets; no private source is sent to the network."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile
import urllib.request

root = Path(__file__).resolve().parents[1]
cache = root / ".vendor"
public = root / "public/vendor"
cache.mkdir(exist_ok=True)
public.mkdir(exist_ok=True, parents=True)
lock = json.loads((root / "documents/assets.lock.json").read_text())
for name, item in lock["downloads"].items():
    path = cache / Path(item["path"]).name
    qualified = root.parent / ".qualification" / item["path"]
    raw = path.read_bytes() if path.exists() else qualified.read_bytes() if qualified.exists() else urllib.request.urlopen(item["url"], timeout=60).read()
    if hashlib.sha256(raw).hexdigest() != item["sha256"]:
        raise RuntimeError(f"Asset digest mismatch: {name}")
    path.write_bytes(raw)
    if name in {"drawio", "drawio_stencils", "drawio_stencil_license", "drawio_license"}:
        shutil.copyfile(path, public / path.name)
with tarfile.open(cache / "pdfjs.tgz", "r:gz") as archive:
    for member in archive.getmembers():
        relative = member.name.removeprefix("package/")
        if not member.isfile() or not (relative in {"build/pdf.mjs", "build/pdf.worker.mjs", "LICENSE"} or relative.startswith(("cmaps/", "standard_fonts/", "wasm/"))):
            continue
        destination = public / "pdfjs" / relative
        if not destination.resolve().is_relative_to((public / "pdfjs").resolve()):
            raise RuntimeError("Invalid vendor path")
        destination.parent.mkdir(exist_ok=True, parents=True)
        destination.write_bytes(archive.extractfile(member).read())
(public / "NOTICES.txt").write_text("draw.io 32.4.1 — Apache-2.0, bundled third-party notices retained in viewer-static.min.js.\nStencils: see STENCILS-LICENSE.\nPDF.js 6.4.299 — Apache-2.0, see pdfjs/LICENSE.\nPlantUML 1.2026.8 MIT distribution — https://plantuml.com/license\nPinned sources and digests: documents/assets.lock.json.\n")
print("Document vendor assets verified and acquired.")
