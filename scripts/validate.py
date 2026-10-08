#!/usr/bin/env python3
"""Validate data/*.csv against data/schema.yaml. Exit code 1 on any error."""
import sys

from ubsi_data import load, validate


def main() -> int:
    datasets = load()
    errors = validate(datasets)
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"\n{len(errors)} error(s)")
        return 1
    counts = ", ".join(f"{d.name}: {len(d.rows)}" for d in datasets.values())
    print(f"OK ({counts})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
