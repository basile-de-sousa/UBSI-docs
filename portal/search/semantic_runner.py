"""Bounded worker child. Input/output are private pipes, never diagnostic logs."""
import json
import os
import sys


def main():
    config = json.load(sys.stdin)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from search.runtime import Inference
    output = []
    with Inference() as engine:
        for row in config["passages"]:
            for ordinal, (start, end, content) in enumerate(engine.chunk(row["title"], row["text"])):
                output.append({"passage": row["id"], "ordinal": ordinal, "start": start, "end": end, "input": content})
                if len(output) > config["max_chunks"]:
                    raise ValueError
        if output:
            vectors = engine.encode([row.pop("input") for row in output])
            for row, vector in zip(output, vectors, strict=True):
                row["embedding"] = vector.astype("<f4").tobytes().hex()
    json.dump(output, sys.stdout)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # No source, stack trace, submitted question or credential leaves the child.
        sys.exit(1)
