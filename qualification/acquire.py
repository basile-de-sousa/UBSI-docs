"""Acquire pinned, public M0 assets into an ignored local directory."""

import hashlib
import json
import os
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".qualification"
LOCK = Path(__file__).with_name("assets.lock.json")


def download(url, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "UBSI-M0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        target.write_bytes(response.read())
    return hashlib.sha256(target.read_bytes()).hexdigest()


def main():
    assets = json.loads(LOCK.read_text())
    for name, item in assets["downloads"].items():
        target = WORK / item["path"]
        if not target.exists():
            digest = download(item["url"], target)
        else:
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
        expected = item.get("sha256")
        if expected and digest != expected:
            raise ValueError(f"Checksum mismatch: {name}")
        item["sha256"] = digest
        print(f"{name}: {target.stat().st_size} bytes", flush=True)
    # Only initialize digests on the first acquisition; later runs verify them.
    LOCK.write_text(json.dumps(assets, indent=2) + "\n")
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    from huggingface_hub import snapshot_download
    for name in ["model", "reranker"]:
        if name not in assets:
            continue
        snapshot_download(
            repo_id=assets[name]["id"], revision=assets[name]["revision"],
            local_dir=WORK / name, allow_patterns=[
                "*.json", "model.safetensors", "sentencepiece.bpe.model", "README.md"
            ],
        )
        print(f"{name} acquired at a pinned revision.", flush=True)


if __name__ == "__main__":
    main()
