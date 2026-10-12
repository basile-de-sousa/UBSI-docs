"""Single isolated preparation invocation; prints safe codes, never source content."""
import json
import os
from pathlib import Path
import resource
import subprocess
import sys


def main():
    config = json.load(sys.stdin)
    # Apply before importing parsers or starting Java. Process group is killed by parent timeout.
    if sys.platform == "linux":
        memory = config["memory_mb"] * 1024**2
        resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    resource.setrlimit(resource.RLIMIT_CPU, (config["seconds"], config["seconds"] + 1))
    resource.setrlimit(resource.RLIMIT_FSIZE, (config["limits"]["expanded_bytes"], config["limits"]["expanded_bytes"]))
    os.umask(0o077)
    from .adapters import prepare, PreparationError, write_json
    try:
        manifest = prepare(Path(config["source"]), config["format"], Path(config["output"]), config["limits"], config["options"], Path(config["vendor"]))
        write_json(Path(config["output"]) / "manifest.json", manifest)
    except PreparationError as error:
        print(json.dumps({"code": error.code, "detail": error.detail})); return 1
    except subprocess.TimeoutExpired:
        print("timeout"); return 1
    except FileNotFoundError:
        print("unavailable"); return 2
    except Exception:
        print("invalid"); return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
