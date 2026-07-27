#!/usr/bin/env python3

import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Copy pico_ota into a MicroPython application's lib directory."
    )
    parser.add_argument(
        "application_root",
        type=Path,
        help="Root directory of the target Pico application",
    )
    args = parser.parse_args()

    source = Path(__file__).resolve().parents[1] / "src" / "pico_ota"
    destination = args.application_root.resolve() / "lib" / "pico_ota"

    if destination.exists():
        shutil.rmtree(destination)

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    print(f"Copied {source} to {destination}")


if __name__ == "__main__":
    main()
