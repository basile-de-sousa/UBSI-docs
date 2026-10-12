"""Acquire public model artifacts with pinned revisions and per-file digests."""
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "search/assets.lock.json").read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


for item in LOCK["files"]:
    target = ROOT / ".models" / item["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if sha(target) != item["sha256"]: raise SystemExit("Model checksum mismatch.")
        continue
    cached = ROOT.parent / ".qualification" / item["path"]
    staging = target.with_suffix(target.suffix + ".partial")
    try:
        if cached.is_file() and sha(cached) == item["sha256"]:
            shutil.copyfile(cached, staging)
        else:
            request = urllib.request.Request(item["url"], headers={"User-Agent": "UBSI-M6"})
            with urllib.request.urlopen(request, timeout=120) as response, staging.open("wb") as stream:
                shutil.copyfileobj(response, stream)
        if sha(staging) != item["sha256"]: raise SystemExit("Model checksum mismatch.")
        staging.replace(target)
    finally:
        staging.unlink(missing_ok=True)
print(f"Verified {len(LOCK['files'])} pinned model artifacts (MIT / Apache-2.0).")
