#!/usr/bin/env python3

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import quote


EXCLUDED_SUFFIXES = (".new", ".bak", ".tmp")
DEFAULT_EXCLUDED_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "secrets.py",
    "device_config.py",
}


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(root, include_paths):
    output = []

    for item in include_paths:
        candidate = (root / item).resolve()

        if not candidate.exists():
            raise FileNotFoundError("Included path does not exist: %s" % item)

        if candidate.is_file():
            output.append(candidate)
            continue

        for child in sorted(candidate.rglob("*")):
            if child.is_file():
                output.append(child)

    unique = []
    seen = set()

    for path in output:
        relative = path.relative_to(root).as_posix()

        if any(part in DEFAULT_EXCLUDED_NAMES for part in path.parts):
            continue
        if path.name in DEFAULT_EXCLUDED_NAMES:
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        if relative in seen:
            continue

        seen.add(relative)
        unique.append(path)

    return sorted(unique)


def build_manifest(root, base_url, application, version, channel, include_paths):
    root = root.resolve()
    files = []

    for path in collect_files(root, include_paths):
        relative = path.relative_to(root).as_posix()
        encoded_path = "/".join(quote(part) for part in relative.split("/"))

        files.append(
            {
                "path": relative,
                "url": base_url.rstrip("/") + "/" + encoded_path,
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
            }
        )

    if not files:
        raise ValueError("No release files were collected")

    return {
        "schema_version": 1,
        "application": application,
        "version": version,
        "channel": channel,
        "files": files,
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--application", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--channel", default="stable")
    parser.add_argument("--include", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    manifest = build_manifest(
        root=args.root,
        base_url=args.base_url,
        application=args.application,
        version=args.version,
        channel=args.channel,
        include_paths=args.include,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Wrote %s with %d files" % (args.output, len(manifest["files"])))


if __name__ == "__main__":
    main()
